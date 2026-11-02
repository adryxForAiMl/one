from app.schemas import Anomaly, CivicEvent, FeedHealth, FeedType, Zone


def summarize_zone(
    zone: Zone,
    events: list[CivicEvent],
    anomalies: list[Anomaly],
    health: list[FeedHealth],
) -> str:
    zone_events = [event for event in events if event.zone_id == zone.id]
    zone_anomalies = [item for item in anomalies if item.zone_id == zone.id]
    down = [item.name for item in health if item.status == "down"]
    stale = [item.name for item in health if item.status == "stale"]

    if zone_anomalies:
        message = zone_anomalies[0].plain_language_note
    elif zone_events:
        message = f"No strong cross-feed pattern is showing in {zone.name}; the latest available signals are being monitored."
    else:
        message = f"There are no recent events for {zone.name} in the available feeds."

    unavailable: list[FeedType] = down + stale
    if unavailable:
        labels = ", ".join(sorted(set(unavailable)))
        message += f" Data from {labels} is currently down or stale, so this view may be incomplete."
    return message