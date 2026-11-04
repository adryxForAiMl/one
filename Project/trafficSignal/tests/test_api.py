import time

from fastapi.testclient import TestClient

from Traffic import api as traffic_api
from Traffic.backend import simulation

app = traffic_api.app
manager = traffic_api.manager


def test_api_idle_and_config_validation():
    manager.reset()
    with TestClient(app) as client:
        health = client.get("/health")
        assert health.status_code == 200
        assert health.json()["status"] == "ok"
        assert isinstance(health.json()["simulation_engine"]["available"], bool)
        assert client.get("/docs").status_code == 200
        assert client.get("/openapi.json").status_code == 200
        vite_preflight = client.options("/api/simulation/start", headers={
            "Origin": "http://127.0.0.1:5175",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        })
        assert vite_preflight.status_code == 200
        assert vite_preflight.headers["access-control-allow-origin"] == "http://127.0.0.1:5175"
        external_preflight = client.options("/api/simulation/start", headers={
            "Origin": "https://example.invalid",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        })
        assert external_preflight.status_code == 400
        state_response = client.get("/api/state")
        state = state_response.json()
        assert state_response.headers["cache-control"] == "no-store"
        assert state["status"] == "idle"
        assert state["simulation_time_seconds"] is None
        assert state["controllers"] == {}
        assert client.post("/api/simulation/pause").status_code == 409
        invalid = client.post("/api/simulation/start", json={
            "controller": {"min_green_seconds": 40, "max_green_seconds": 20}
        })
        assert invalid.status_code == 422
        invalid_speed = client.post("/api/simulation/start", json={"speed_multiplier": 12})
        assert invalid_speed.status_code == 422


def test_health_reports_missing_sumo_binary(monkeypatch):
    traffic_api.sumo_runtime_status.cache_clear()
    monkeypatch.setattr(traffic_api, "find_sumo_binary", lambda: "/missing/sumo")
    with TestClient(app) as client:
        health = client.get("/health").json()
    traffic_api.sumo_runtime_status.cache_clear()
    assert health["status"] == "ok"
    assert health["simulation_engine"]["available"] is False
    assert health["simulation_engine"]["traci_available"] is True
    assert "SUMO executable was not found" in health["simulation_engine"]["error"]


def test_configured_cors_origins_are_added(monkeypatch):
    monkeypatch.setenv("TRAFFIC_CORS_ORIGINS", "https://traffic.example, https://preview.example ")
    origins = traffic_api.allowed_cors_origins()
    assert "https://traffic.example" in origins
    assert "https://preview.example" in origins
    assert "http://localhost:5173" in origins


def test_health_disables_simulations_in_vercel_functions(monkeypatch):
    traffic_api.sumo_runtime_status.cache_clear()
    monkeypatch.setenv("VERCEL", "1")
    with TestClient(app) as client:
        health = client.get("/health").json()
    assert health["status"] == "ok"
    assert health["simulation_runtime"]["suitable_for_long_running"] is False
    assert "persistent process" in health["simulation_runtime"]["error"]


def test_api_simulation_state_and_websocket_use_live_sumo_data():
    manager.reset()
    with TestClient(app) as client:
        response = client.post("/api/simulation/start", json={
            "mode": "adaptive", "scenario": "balanced", "seed": 101,
            "duration_seconds": 15,
        })
        assert response.status_code == 200
        assert response.json()["status"] == "connecting"
        assert response.json()["speed_multiplier"] == 8.0
        duplicate = client.post("/api/simulation/start", json={"duration_seconds": 15})
        assert duplicate.status_code == 409

        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            state = client.get("/api/state").json()
            if state["status"] in {"completed", "disconnected", "stopped"}:
                break
            time.sleep(0.05)

        assert state["status"] == "completed"
        assert state["simulation_time_seconds"] == 15.0
        adaptive = state["controllers"]["adaptive"]
        assert adaptive["signal"]["phase_state"]
        assert adaptive["metrics"]["active_vehicles"] >= 0
        assert adaptive["metrics"]["average_completed_trip_travel_time_seconds"] >= 0
        assert state["results_summary"]["adaptive"]["total_completed_trips"] == adaptive["metrics"]["completed_vehicles"]
        assert state["results_summary"]["adaptive"]["average_completed_trip_travel_time_seconds"] >= 0
        if adaptive["vehicles"]:
            assert {"vehicle_id", "x_m", "y_m", "speed_mps"}.issubset(adaptive["vehicles"][0])

        with client.websocket_connect("/ws/live") as websocket:
            message = websocket.receive_json()
            assert message["status"] == "completed"
            assert message["controllers"]["adaptive"]["signal"]["phase_state"]
    manager.reset()


def test_api_reports_disconnected_when_sumo_start_fails(monkeypatch):
    manager.reset()

    def fail_start(*_args, **_kwargs):
        raise RuntimeError("SUMO offline")

    monkeypatch.setattr(simulation.traci, "start", fail_start)
    with TestClient(app) as client:
        response = client.post("/api/simulation/start", json={
            "mode": "fixed", "duration_seconds": 5, "seed": 5,
        })
        assert response.status_code == 200
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            state = client.get("/api/state").json()
            if state["status"] == "disconnected":
                break
            time.sleep(0.02)
        assert state["status"] == "disconnected"
        assert "SUMO offline" in state["error"]
    manager.reset()
