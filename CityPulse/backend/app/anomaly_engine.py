from datetime import datetime, timedelta, timezone

from app.schemas import Anomaly, CivicEvent, FeedHealth, FeedType, Zone


class AnomalyEngine:
    """Explainable co-occurrence rules; confidence is heuristic, not calibrated probability."""

    def detect(
        self,
        events: list[CivicEvent],
        zones: list[Zone],
        health: list[FeedHealth],
        now: datetime | None = None,
    ) -> list[Anomaly]:
        now = now or datetime.now(timezone.utc)
        unavailable_feeds = {item.name for item in health if item.status != "ok"}
        usable = [event for event in events if event.feed_type not in unavailable_feeds]
        anomalies: list[Anomaly] = []

        for zone in zones:
            zone_events = [event for event in usable if event.zone_id == zone.id]
            recent_cutoff = now - timedelta(minutes=15)
            baseline_cutoff = now - timedelta(hours=24)
            recent_complaints = [
                event for event in zone_events
                if event.feed_type == "complaints" and recent_cutoff <= event.timestamp <= now
            ]
            baseline_complaints = [
                event for event in zone_events
                if event.feed_type == "complaints" and baseline_cutoff <= event.timestamp < recent_cutoff
            ]
            expected_count = max(0.5, len(baseline_complaints) / 95)
            complaint_ratio = len(recent_complaints) / expected_count
            weather_active = any(
                event.feed_type == "weather"
                and event.severity >= 0.55
                and now - timedelta(minutes=60) <= event.timestamp <= now
                for event in zone_events
            )
            transit_spike = any(
                event.feed_type == "transit"
                and event.severity >= 0.55
                and now - timedelta(minutes=30) <= event.timestamp <= now
                for event in zone_events
            )

            complaint_cluster = len(recent_complaints) >= 2 and complaint_ratio > 2
            if not complaint_cluster or not (weather_active or transit_spike):
                continue

            feeds_involved: list[FeedType] = ["complaints"]
            if weather_active:
                feeds_involved.append("weather")
            if transit_spike:
                feeds_involved.append("transit")
            evidence_count = len(feeds_involved)
            confidence = min(0.94, 0.58 + 0.09 * (evidence_count - 2) + min(0.15, (complaint_ratio - 2) * 0.015))
            anomaly_time = max(event.timestamp for event in recent_complaints)
            linked_signals = " and ".join(
                {"weather": "a weather alert", "transit": "a transit delay"}[feed]
                for feed in feeds_involved if feed != "complaints"
            )
            note = (
                f"Resident reports are running about {complaint_ratio:.1f}x the recent baseline in {zone.name}, "
                f"alongside {linked_signals}. These signals may be linked; this does not establish a cause."
            )
            anomalies.append(
                Anomaly(
                    zone_id=zone.id,
                    feeds_involved=feeds_involved,
                    confidence=round(confidence, 2),
                    plain_language_note=note,
                    observed_at=anomaly_time,
                )
            )
        return anomalies


def pulse_score(
    zone_id: str,
    events: list[CivicEvent],
    anomalies: list[Anomaly],
    unavailable_feeds: set[FeedType],
) -> int:
    weights = {"weather": 0.35, "transit": 0.3, "complaints": 0.2}
    zone_events = [event for event in events if event.zone_id == zone_id and event.feed_type not in unavailable_feeds]
    signals: dict[FeedType, float] = {
        "weather": max((event.severity for event in zone_events if event.feed_type == "weather"), default=0.0),
        "transit": max((event.severity for event in zone_events if event.feed_type == "transit"), default=0.0),
        "complaints": min(1.0, sum(event.feed_type == "complaints" for event in zone_events) / 4),
    }
    available = [feed for feed in weights if feed not in unavailable_feeds]
    denominator = sum(weights[feed] for feed in available)
    activity = sum(weights[feed] * signals[feed] for feed in available) / denominator if denominator else 0.0
    zone_anomalies = [item.confidence for item in anomalies if item.zone_id == zone_id]
    anomaly_signal = max(zone_anomalies, default=0.0)
    score = 100 * (0.85 * activity + 0.15 * anomaly_signal)
    return max(0, min(100, round(score)))