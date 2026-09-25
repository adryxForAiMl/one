from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_authentication_routes():
    response = client.post("/auth/login", json={"username": "testuser", "password": "testpass"})
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_scan_routes():
    response = client.post("/scans", json={"url": "http://example.com"})
    assert response.status_code == 201
    assert "scan_id" in response.json()

def test_findings_routes():
    response = client.get("/findings")
    assert response.status_code == 200
    assert isinstance(response.json(), list)  # Expecting a list of findings

def test_invalid_route():
    response = client.get("/invalid-route")
    assert response.status_code == 404