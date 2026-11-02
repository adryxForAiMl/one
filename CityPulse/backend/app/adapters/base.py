from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone

from app.schemas import CivicEvent, FeedHealth, FeedType


class FeedAdapter(ABC):
    def __init__(
        self,
        name: FeedType,
        interval_seconds: int,
        stale_after_seconds: int,
        source_mode: str,
    ) -> None:
        self.name = name
        self.interval_seconds = interval_seconds
        self.stale_after_seconds = stale_after_seconds
        self.source_mode = source_mode
        self.is_down = False
        self.last_success_at: datetime | None = None
        self.last_error: str | None = None

    async def poll_once(self) -> list[CivicEvent]:
        if self.is_down:
            return []
        now = datetime.now(timezone.utc)
        try:
            events = await self.collect(now)
        except Exception as error:
            self.last_error = str(error)
            return []
        self.last_success_at = now
        self.last_error = None
        return events

    @abstractmethod
    async def collect(self, now: datetime) -> list[CivicEvent]:
        raise NotImplementedError

    def toggle(self, down: bool | None = None) -> bool:
        self.is_down = not self.is_down if down is None else down
        return self.is_down

    def health(self, now: datetime | None = None) -> FeedHealth:
        now = now or datetime.now(timezone.utc)
        if self.is_down:
            status = "down"
            message = "Manually paused for the demo."
        elif self.last_success_at is None or (
            now - self.last_success_at > timedelta(seconds=self.stale_after_seconds)
        ):
            status = "stale"
            message = self.last_error or "Waiting for the first successful update."
        else:
            status = "ok"
            message = "Receiving updates."
        return FeedHealth(
            name=self.name,
            status=status,
            source_mode=self.source_mode,
            last_success_at=self.last_success_at,
            stale_after_seconds=self.stale_after_seconds,
            message=message,
        )