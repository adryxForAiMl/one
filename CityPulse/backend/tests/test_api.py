from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from app.adapters.weather import WeatherAdapter
from app.main import make_app


async def skip_external_weather(self, now):
    return []


def test_seeded_pulse_and_feed_degradation(monkeypatch):
    monkeypatch.setattr(WeatherAdapter, "collect", skip_external_weather)
    app = make_app()

    with TestClient(app) as client:
        pulse_response = client.get("/api/pulse")
        assert pulse_response.status_code == 200
        pulse = pulse_response.json()
        assert pulse["city"] == "Rajasthan"
        assert len(pulse["zones"]) == 3
        assert all(0 <= zone["pulse_score"] <= 100 for zone in pulse["zones"])

        zone = client.get("/api/zone/zone-3").json()
        assert {event["feed_type"] for event in zone["feeds"]} == {"weather", "transit", "complaints"}
        anomaly = zone["anomalies"][0]
        assert set(anomaly["feeds_involved"]) == {"weather", "transit", "complaints"}
        assert anomaly["is_correlation_not_causation"] is True
        assert "may be linked" in anomaly["plain_language_note"]

        down = client.post("/api/debug/feed/transit/toggle", json={"down": True})
        assert down.json()["status"] == "down"
        degraded_pulse = client.get("/api/pulse").json()
        assert degraded_pulse["zones"][2]["pulse_score"] > 0

        revived = client.post("/api/debug/feed/transit/toggle", json={"down": False})
        assert revived.json()["status"] == "ok"

        app.state.adapters["transit"].last_success_at = datetime.now(timezone.utc) - timedelta(minutes=10)
        stale_status = client.get("/api/feeds/status").json()
        assert next(item for item in stale_status if item["name"] == "transit")["status"] == "stale"
        stale_pulse = client.get("/api/pulse").json()
        jaipur = next(item for item in stale_pulse["zones"] if item["zone_id"] == "zone-3")
        assert jaipur["name"] == "Jaipur"
        assert "transit" in jaipur["stale_feeds"]
        assert jaipur["pulse_score"] > 0


def test_replay_includes_seeded_hero_scenario(monkeypatch):
    monkeypatch.setattr(WeatherAdapter, "collect", skip_external_weather)
    with TestClient(make_app()) as client:
        response = client.get("/api/replay?range=24h")
        assert response.status_code == 200
        replay = response.json()
        assert replay["hero_scenario"]["simulated"] is True
        hero_events = [event for event in replay["events"] if event["zone_id"] == "zone-3"]
        assert {event["feed_type"] for event in hero_events} == {"weather", "transit", "complaints"}