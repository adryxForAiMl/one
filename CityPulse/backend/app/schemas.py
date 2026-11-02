from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


FeedType = Literal["weather", "transit", "complaints"]


class CivicEvent(BaseModel):
    id: str
    feed_type: FeedType
    zone_id: str
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    timestamp: datetime
    severity: float = Field(ge=0, le=1)
    raw_payload: dict[str, Any]

    @field_validator("timestamp")
    @classmethod
    def normalize_timestamp(cls, value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)


class Zone(BaseModel):
    id: str
    name: str
    lat: float
    lon: float


class Anomaly(BaseModel):
    zone_id: str
    feeds_involved: list[FeedType]
    confidence: float = Field(ge=0, le=1)
    plain_language_note: str
    is_correlation_not_causation: Literal[True] = True
    observed_at: datetime


class FeedHealth(BaseModel):
    name: FeedType
    status: Literal["ok", "stale", "down"]
    source_mode: str
    last_success_at: datetime | None
    stale_after_seconds: int
    message: str


class ZonePulse(BaseModel):
    zone_id: str
    name: str
    pulse_score: int = Field(ge=0, le=100)
    status: Literal["calm", "watch", "elevated"]
    summary: str
    active_anomalies: int
    event_count_24h: int
    available_feeds: list[FeedType]
    stale_feeds: list[FeedType]


class PulseResponse(BaseModel):
    as_of: datetime
    city: str
    zones: list[ZonePulse]
    top_summary: str


class FeedToggleRequest(BaseModel):
    down: bool | None = None