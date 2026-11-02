from datetime import datetime
from random import Random
from uuid import uuid4

from app.adapters.base import FeedAdapter
from app.schemas import CivicEvent, Zone


class TransitAdapter(FeedAdapter):
    def __init__(self, zones: list[Zone]) -> None:
        super().__init__("transit", interval_seconds=60, stale_after_seconds=5 * 60, source_mode="synthetic")
        self.zones = zones
        self.random = Random(42)

    async def collect(self, now: datetime) -> list[CivicEvent]:
        events = []
        for zone in self.zones:
            delay_minutes = self.random.choices([0, 4, 9, 18], weights=[45, 30, 18, 7])[0]
            events.append(
                CivicEvent(
                    id=str(uuid4()),
                    feed_type="transit",
                    zone_id=zone.id,
                    lat=zone.lat,
                    lon=zone.lon,
                    timestamp=now,
                    severity=min(1.0, delay_minutes / 25),
                    raw_payload={
                        "source": "CityPulse synthetic transit feed",
                        "event_type": "transit_delay",
                        "delay_minutes": delay_minutes,
                        "simulated": True,
                    },
                )
            )
        return events


class ComplaintsAdapter(FeedAdapter):
    def __init__(self, zones: list[Zone]) -> None:
        super().__init__("complaints", interval_seconds=17, stale_after_seconds=3 * 60, source_mode="synthetic")
        self.zones = zones
        self.random = Random(311)

    async def collect(self, now: datetime) -> list[CivicEvent]:
        if self.random.random() > 0.003:
            return []
        zone = self.random.choice(self.zones)
        category = self.random.choice(["road obstruction", "waterlogging", "streetlight outage"])
        severity = self.random.uniform(0.18, 0.5)
        return [
            CivicEvent(
                id=str(uuid4()),
                feed_type="complaints",
                zone_id=zone.id,
                lat=zone.lat,
                lon=zone.lon,
                timestamp=now,
                severity=severity,
                raw_payload={
                    "source": "CityPulse synthetic 311-style feed",
                    "event_type": "resident_report",
                    "category": category,
                    "simulated": True,
                },
            )
        ]