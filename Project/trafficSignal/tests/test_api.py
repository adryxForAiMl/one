import time

from fastapi.testclient import TestClient

from Traffic.api import app, manager
from Traffic.backend import simulation


def test_api_idle_and_config_validation():
    manager.reset()
    with TestClient(app) as client:
        assert client.get("/health").json() == {"status": "ok"}
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
