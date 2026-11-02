import asyncio
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.adapters.base import FeedAdapter
from app.adapters.synthetic import ComplaintsAdapter, TransitAdapter
from app.adapters.weather import WeatherAdapter
from app.anomaly_engine import AnomalyEngine, pulse_score
from app.schemas import (
    Anomaly,
    CivicEvent,
    FeedHealth,
    FeedToggleRequest,
    FeedType,
    PulseResponse,
    Zone,
    ZonePulse,
)
from app.summary import summarize_zone


CITY = "Rajasthan"
ZONES = [
    Zone(id="zone-1", name="Ajmer", lat=26.4499, lon=74.6399),
    Zone(id="zone-2", name="Jodhpur", lat=26.2389, lon=73.0243),
    Zone(id="zone-3", name="Jaipur", lat=26.9124, lon=75.7873),
]
ROLLING_WINDOW = timedelta(hours=24)
FEED_TYPES: tuple[FeedType, ...] = ("weather", "transit", "complaints")


class EventStore:
    def __init__(self) -> None:
        self.events: list[CivicEvent] = []

    def add_many(self, events: list[CivicEvent], now: datetime | None = None) -> None:
        now = now or datetime.now(timezone.utc)
        cutoff = now - ROLLING_WINDOW
        self.events.extend(events)
        self.events = [event for event in self.events if event.timestamp >= cutoff]

    def recent(self, now: datetime | None = None) -> list[CivicEvent]:
        now = now or datetime.now(timezone.utc)
        cutoff = now - ROLLING_WINDOW
        self.events = [event for event in self.events if event.timestamp >= cutoff]
        return list(self.events)


def seed_demo_events(now: datetime) -> list[CivicEvent]:
    events: list[CivicEvent] = []

    def add(feed: FeedType, zone: Zone, when: datetime, severity: float, payload: dict) -> None:
        events.append(
            CivicEvent(
                id=str(uuid4()), feed_type=feed, zone_id=zone.id,
                lat=zone.lat, lon=zone.lon, timestamp=when,
                severity=severity, raw_payload={**payload, "simulated": True},
            )
        )

    for index, zone in enumerate(ZONES):
        add("weather", zone, now - timedelta(minutes=2), 0.16 + index * 0.04,
            {"source": "CityPulse seeded replay", "event_type": "weather_observation", "precipitation_mm": 3 + index})
        add("transit", zone, now - timedelta(minutes=1), 0.14 + index * 0.05,
            {"source": "CityPulse seeded replay", "event_type": "transit_delay", "delay_minutes": 3 + index})
        add("complaints", zone, now - timedelta(hours=3), 0.2,
            {"source": "CityPulse seeded replay", "event_type": "resident_report", "category": "road maintenance"})

    for days_ago in (2, 1):
        for index, zone in enumerate(ZONES):
            day = timedelta(days=days_ago)
            add("weather", zone, now - day - timedelta(hours=5), 0.22 + index * 0.08,
                {"source": "CityPulse seeded history", "event_type": "rain_observation", "precipitation_mm": 4 + index * 2})
            add("transit", zone, now - day - timedelta(hours=4), 0.18 + index * 0.04,
                {"source": "CityPulse seeded history", "event_type": "transit_delay", "delay_minutes": 4 + index})
            add("complaints", zone, now - day - timedelta(hours=2), 0.2,
                {"source": "CityPulse seeded history", "event_type": "resident_report", "category": "street maintenance"})

    hero = next(zone for zone in ZONES if zone.id == "zone-3")
    add("weather", hero, now - timedelta(minutes=4), 0.82,
        {"source": "CityPulse seeded hero scenario", "event_type": "heavy_rain_alert", "precipitation_mm": 24})
    add("transit", hero, now - timedelta(minutes=2), 0.76,
        {"source": "CityPulse seeded hero scenario", "event_type": "transit_delay", "delay_minutes": 19})
    for offset in (50, 35, 20, 5):
        add("complaints", hero, now - timedelta(seconds=offset), 0.62,
            {"source": "CityPulse seeded hero scenario", "event_type": "resident_report", "category": "waterlogging"})

    for offset in (30, 18):
        add("complaints", hero, now - timedelta(hours=offset), 0.22,
            {"source": "CityPulse seeded baseline", "event_type": "resident_report", "category": "road maintenance"})
    return events


async def poll_forever(adapter: FeedAdapter, store: EventStore) -> None:
    while True:
        await asyncio.sleep(adapter.interval_seconds)
        if adapter.is_down:
            continue
        store.add_many(await adapter.poll_once())


def make_app() -> FastAPI:
    store = EventStore()
    adapters: dict[FeedType, FeedAdapter] = {
        "weather": WeatherAdapter(ZONES),
        "transit": TransitAdapter(ZONES),
        "complaints": ComplaintsAdapter(ZONES),
    }
    engine = AnomalyEngine()
    replay_events: list[CivicEvent] = []
    tasks: list[asyncio.Task] = []

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        nonlocal replay_events
        now = datetime.now(timezone.utc)
        replay_events = seed_demo_events(now)
        store.add_many(replay_events, now)
        await asyncio.gather(*(adapter.poll_once() for adapter in adapters.values()))
        for adapter in adapters.values():
            tasks.append(asyncio.create_task(poll_forever(adapter, store)))
        app.state.store = store
        app.state.adapters = adapters
        app.state.zones = ZONES
        app.state.engine = engine
        app.state.replay_events = replay_events
        yield
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    app = FastAPI(title="CityPulse API", version="0.1.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    def snapshot() -> tuple[datetime, list[CivicEvent], list[FeedHealth], list[Anomaly]]:
        now = datetime.now(timezone.utc)
        events = store.recent(now)
        health = [adapter.health(now) for adapter in adapters.values()]
        anomalies = engine.detect(events, ZONES, health, now)
        return now, events, health, anomalies

    def build_zone_pulse(zone: Zone, events: list[CivicEvent], health: list[FeedHealth], anomalies: list[Anomaly]) -> ZonePulse:
        unavailable_feeds = {item.name for item in health if item.status != "ok"}
        score = pulse_score(zone.id, events, anomalies, unavailable_feeds)
        zone_events = [event for event in events if event.zone_id == zone.id]
        active_count = sum(item.zone_id == zone.id for item in anomalies)
        status = "elevated" if score >= 65 else "watch" if score >= 35 else "calm"
        return ZonePulse(
            zone_id=zone.id,
            name=zone.name,
            pulse_score=score,
            status=status,
            summary=summarize_zone(zone, events, anomalies, health),
            active_anomalies=active_count,
            event_count_24h=len(zone_events),
            available_feeds=[item.name for item in health if item.status != "down"],
            stale_feeds=[item.name for item in health if item.status != "ok"],
        )

    def pulse_from_snapshot(
        now: datetime,
        events: list[CivicEvent],
        health: list[FeedHealth],
        anomalies: list[Anomaly],
    ) -> PulseResponse:
        zones = [build_zone_pulse(zone, events, health, anomalies) for zone in ZONES]
        top = max(zones, key=lambda item: item.pulse_score)
        return PulseResponse(as_of=now, city=CITY, zones=zones, top_summary=top.summary)

    def pulse_payload() -> PulseResponse:
        return pulse_from_snapshot(*snapshot())

    @app.get("/api/health")
    async def api_health() -> dict[str, str]:
        return {"status": "ok", "service": "citypulse-api"}

    @app.get("/api/pulse", response_model=PulseResponse)
    async def get_pulse() -> PulseResponse:
        return pulse_payload()

    @app.get("/api/zone/{zone_id}")
    async def get_zone(zone_id: str) -> dict:
        zone = next((item for item in ZONES if item.id == zone_id), None)
        if zone is None:
            raise HTTPException(status_code=404, detail="Unknown zone")
        now, events, health, anomalies = snapshot()
        zone_events = [event for event in events if event.zone_id == zone_id]
        zone_anomalies = [item for item in anomalies if item.zone_id == zone_id]
        return {
            "zone": zone,
            "pulse": build_zone_pulse(zone, events, health, anomalies),
            "feeds": zone_events,
            "anomalies": zone_anomalies,
            "summary": summarize_zone(zone, events, anomalies, health),
            "as_of": now,
        }

    @app.get("/api/feeds/status", response_model=list[FeedHealth])
    async def get_feed_status() -> list[FeedHealth]:
        now = datetime.now(timezone.utc)
        return [adapter.health(now) for adapter in adapters.values()]

    @app.get("/api/summary/{zone_id}")
    async def get_summary(zone_id: str) -> dict[str, str]:
        zone = next((item for item in ZONES if item.id == zone_id), None)
        if zone is None:
            raise HTTPException(status_code=404, detail="Unknown zone")
        _, events, health, anomalies = snapshot()
        return {"zone_id": zone_id, "summary": summarize_zone(zone, events, anomalies, health)}

    @app.get("/api/replay")
    async def get_replay(range: str = Query(default="72h", pattern="^(6h|24h|72h)$")) -> dict:
        hours = int(range[:-1])
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(hours=hours)
        events = [event for event in replay_events if cutoff <= event.timestamp <= now]
        return {
            "range": range,
            "events": sorted(events, key=lambda item: item.timestamp),
            "hero_scenario": {
                "zone_id": "zone-3",
                "sequence": ["weather alert", "transit delay", "complaint spike"],
                "simulated": True,
            },
        }

    @app.post("/api/debug/feed/{name}/toggle")
    async def toggle_feed(name: str, request: FeedToggleRequest | None = None) -> dict:
        if name not in adapters:
            raise HTTPException(status_code=404, detail="Unknown feed")
        adapter = adapters[name]
        is_down = adapter.toggle(request.down if request else None)
        if not is_down:
            store.add_many(await adapter.poll_once())
        return {"feed": name, "status": adapter.health().status, "message": adapter.health().message}

    @app.websocket("/ws/pulse")
    async def websocket_pulse(websocket: WebSocket) -> None:
        await websocket.accept()
        try:
            while True:
                now, events, health, anomalies = snapshot()
                await websocket.send_json(
                    {
                        "pulse": pulse_from_snapshot(now, events, health, anomalies).model_dump(mode="json"),
                        "feeds": [item.model_dump(mode="json") for item in health],
                        "anomalies": [item.model_dump(mode="json") for item in anomalies],
                        "recent_events": [item.model_dump(mode="json") for item in sorted(events, key=lambda event: event.timestamp)[-12:]],
                    }
                )
                await asyncio.sleep(2)
        except WebSocketDisconnect:
            return

    return app


app = make_app()