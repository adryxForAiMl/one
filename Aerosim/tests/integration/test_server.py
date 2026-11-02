import pytest
from fastapi.testclient import TestClient
from aerosim.server import app

client = TestClient(app)


def test_api_status_endpoint():
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "telemetry" in data
    assert "operation_mode" in data


def test_api_locations_endpoint():
    response = client.get("/api/locations")
    assert response.status_code == 200
    data = response.json()
    assert "presets" in data
    assert "new_delhi" in data["presets"]
    assert "mumbai" in data["presets"]


def test_api_ports_endpoint():
    response = client.get("/api/ports")
    assert response.status_code == 200
    data = response.json()
    assert "ports" in data
