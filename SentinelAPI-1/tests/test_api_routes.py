from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_auth_routes():
    # Add tests for authentication routes
    response = client.post("/auth/login", json={"username": "testuser", "password": "testpass"})
    assert response.status_code in [200, 201]
    assert "access_token" in response.json()

def test_scan_routes():
    # Add tests for scan routes
    response = client.get("/scans")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_report_routes():
    # Add tests for report routes
    response = client.get("/reports")
    assert response.status_code == 200
    assert isinstance(response.json(), list)