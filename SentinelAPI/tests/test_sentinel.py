"""
SentinelAPI Automated Test Suite.
Validates:
- OpenAPI and Swagger specification parsing
- Target Preflight validation and checklists
- Deterministic BOLA authorization scanning
- Local Random Forest ML model inference and Risk Engine
- Posture Scorecard calculation
- Export capabilities
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.intelligence.risk_engine import (
    FEATURE_NAMES,
    ML_MODEL,
    build_security_scorecard,
    calculate_intelligent_risk,
    explain_risk_score,
)
from app.main import app
from app.scanner.bola_scanner import (
    detect_sensitive_fields,
    find_object_endpoints,
    mask_credential,
    mask_headers,
)
from app.scanner.openapi_parser import OpenAPIParser
from app.scanner.target_preflight import normalize_target_url, run_target_preflight
from sandbox.main import app as sandbox_app


client = TestClient(app)
sandbox_client = TestClient(sandbox_app)


SAMPLE_OPENAPI_SPEC = {
    "openapi": "3.0.2",
    "info": {
        "title": "Sample E-Commerce API",
        "version": "1.0.0",
    },
    "paths": {
        "/orders": {
            "get": {
                "summary": "List my orders",
                "responses": {"200": {"description": "Order list"}},
            }
        },
        "/orders/{order_id}": {
            "get": {
                "summary": "Get specific order",
                "parameters": [
                    {
                        "name": "order_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "integer"},
                    }
                ],
                "responses": {"200": {"description": "Order details"}},
            }
        },
        "/users": {
            "get": {
                "summary": "List users",
                "responses": {"200": {"description": "Users"}},
            }
        },
        "/users/{id}": {
            "get": {
                "summary": "User profile",
                "parameters": [
                    {
                        "name": "id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "integer"},
                    }
                ],
            }
        },
    },
}


def test_openapi_parser():
    """Verify OpenAPI 3.x ingestion, normalization, and endpoint classification."""
    parser = OpenAPIParser(SAMPLE_OPENAPI_SPEC)
    assert parser.version == "3.0.2"
    assert parser.title == "Sample E-Commerce API"
    assert len(parser.endpoints) == 4

    object_eps = parser.get_object_endpoints()
    assert len(object_eps) == 2
    paths = {ep.path for ep in object_eps}
    assert "/orders/{order_id}" in paths
    assert "/users/{id}" in paths

    order_obj = next(ep for ep in object_eps if ep.path == "/orders/{order_id}")
    paired = parser.find_paired_collection(order_obj)
    assert paired is not None
    assert paired.path == "/orders"


def test_target_url_normalization():
    """Test URL normalization edge cases."""
    assert normalize_target_url("localhost:8000") == "http://localhost:8000"
    assert normalize_target_url("http://127.0.0.1:8000/") == "http://127.0.0.1:8000"
    assert normalize_target_url("https://api.example.com/v1///") == "https://api.example.com/v1"

    with pytest.raises(ValueError):
        normalize_target_url("")


def test_mask_credential():
    """Verify secrets are never stored or displayed unmasked."""
    assert mask_credential(None) == "[NONE]"
    assert mask_credential("short") == "***"
    assert mask_credential("token-user-a") == "tok***-a"

    headers = {"Authorization": "Bearer secret-12345", "Content-Type": "application/json"}
    masked = mask_headers(headers)
    assert masked["Content-Type"] == "application/json"
    assert "secret-12345" not in masked["Authorization"]


def test_detect_sensitive_fields():
    """Verify excessive data exposure detection for sensitive keys."""
    data = {
        "order_id": 101,
        "product": "Laptop",
        "user_email": "admin@example.com",
        "auth_token": "xyz789",
    }
    exposed = detect_sensitive_fields(data)
    assert "user_email" in exposed
    assert "auth_token" in exposed
    assert "order_id" not in exposed


def test_ml_risk_model_inference():
    """Ensure local scikit-learn Random Forest model generates valid probabilities."""
    assert ML_MODEL is not None
    dummy_features = {name: 1.0 for name in FEATURE_NAMES}

    findings = [
        {
            "id": "BOLA-001",
            "type": "BOLA",
            "severity": "CRITICAL",
            "status_code": 200,
            "endpoint": "/orders/102",
            "method": "GET",
            "attacker": "User A",
            "resource_owner": "User B",
            "object_id": 102,
            "verification": {
                "cross_identity": True,
                "ownership_mismatch": True,
                "successful_access": True,
                "object_identity_matched": True,
            },
            "evidence": {
                "request": {"method": "GET"},
                "response": {"order_id": 102, "owner_id": 2},
            },
        }
    ]
    endpoints = [
        {"path": "/orders", "method": "GET", "category": "collection"},
        {"path": "/orders/{order_id}", "method": "GET", "category": "object", "authorization_tested": True},
    ]

    result = calculate_intelligent_risk(findings, endpoints)
    assert result["score"] >= 80
    assert result["level"] == "CRITICAL"
    assert result["confidence_label"] in ("HIGH", "VERY HIGH")
    assert "WHY:" in result["why_explanation"]

    scorecard = result["scorecard"]
    assert scorecard["overall_grade"] == "F"  # Fails due to verified BOLA
    categories = {c["name"]: c for c in scorecard["categories"]}
    assert categories["Authorization"]["status"] == "VIOLATED"


def test_fastapi_endpoints():
    """Verify SentinelAPI FastAPI routes."""
    res = client.get("/")
    assert res.status_code == 200
    assert res.json()["name"] == "SentinelAPI"

    health_res = client.get("/health")
    assert health_res.status_code == 200
    assert health_res.json()["status"] == "healthy"

    # Preflight against non-existent port should return NETWORK_ERROR cleanly
    preflight_res = client.post("/preflight", json={"target_url": "http://127.0.0.1:59999"})
    assert preflight_res.status_code == 200
    preflight_data = preflight_res.json()
    assert preflight_data["status"] == "NETWORK_ERROR"
    assert len(preflight_data["checklist"]) > 0


def test_sandbox_endpoints():
    """Verify Sandbox API behavior with authorized and cross-user requests."""
    # Test valid user A fetching orders
    res_a = sandbox_client.get("/orders", headers={"Authorization": "token-user-a"})
    assert res_a.status_code == 200
    orders_a = res_a.json()
    assert len(orders_a) == 1
    assert orders_a[0]["order_id"] == 101

    # Test valid user B fetching orders
    res_b = sandbox_client.get("/orders", headers={"Authorization": "token-user-b"})
    assert res_b.status_code == 200
    orders_b = res_b.json()
    assert len(orders_b) == 1
    assert orders_b[0]["order_id"] == 102

    # Test BOLA vulnerability: User A accessing User B's order 102
    res_bola = sandbox_client.get("/orders/102", headers={"Authorization": "token-user-a"})
    assert res_bola.status_code == 200
    assert res_bola.json()["order_id"] == 102
    assert res_bola.json()["owner_id"] == 2  # Belongs to user B!
