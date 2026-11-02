from datetime import datetime, timezone
from uuid import uuid4

import httpx

from app.adapters.base import FeedAdapter
from app.schemas import CivicEvent, Zone


class WeatherAdapter(FeedAdapter):
    def __init__(self, zones: list[Zone]) -> None:
        super().__init__("weather", interval_seconds=4 * 60 * 60, stale_after_seconds=8 * 60 * 60, source_mode="open-meteo")
        self.zones = zones

    async def collect(self, now: datetime) -> list[CivicEvent]:
        events: list[CivicEvent] = []
        async with httpx.AsyncClient(timeout=4.0) as client:
            for zone in self.zones:
                try:
                    response = await client.get(
                        "https://api.open-meteo.com/v1/forecast",
                        params={
                            "latitude": zone.lat,
                            "longitude": zone.lon,
                            "current": "precipitation,relative_humidity_2m",
                            "timezone": "UTC",
                        },
                    )
                    response.raise_for_status()
                    current = response.json()["current"]
                    rain_mm = float(current.get("precipitation") or 0)
                    event_time = datetime.fromisoformat(current["time"]).replace(tzinfo=timezone.utc)
                    self.source_mode = "open-meteo"
                    events.append(
                        CivicEvent(
                            id=str(uuid4()),
                            feed_type="weather",
                            zone_id=zone.id,
                            lat=zone.lat,
                            lon=zone.lon,
                            timestamp=event_time,
                            severity=min(1.0, rain_mm / 20.0),
                            raw_payload={
                                "source": "Open-Meteo",
                                "event_type": "rain_observation",
                                "precipitation_mm": rain_mm,
                                "relative_humidity_percent": current.get("relative_humidity_2m"),
                                "simulated": False,
                            },
                        )
                    )
                except (httpx.HTTPError, KeyError, TypeError, ValueError):
                    events.append(self._fallback_event(zone, now))
        if any(event.raw_payload.get("simulated") for event in events):
            self.source_mode = "synthetic fallback"
        else:
            self.source_mode = "open-meteo"
        return events

    @staticmethod
    def _fallback_event(zone: Zone, now: datetime) -> CivicEvent:
        return CivicEvent(
            id=str(uuid4()),
            feed_type="weather",
            zone_id=zone.id,
            lat=zone.lat,
            lon=zone.lon,
            timestamp=now,
            severity=0.12,
            raw_payload={
                "source": "CityPulse synthetic fallback",
                "event_type": "weather_unavailable",
                "precipitation_mm": None,
                "simulated": True,
            },
        )