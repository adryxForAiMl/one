import pytest
from httpx import Response
from app.scanner.bola_scanner import scan_bola

@pytest.fixture
def mock_credentials():
    return {
        "user1": "valid_token_user1",
        "user2": "valid_token_user2",
    }

@pytest.fixture
def mock_base_url():
    return "http://localhost:8000"

def test_scan_bola_success(mock_base_url, mock_credentials):
    findings = scan_bola(mock_base_url, mock_credentials)
    assert isinstance(findings, list)
    assert all(isinstance(finding, dict) for finding in findings)

def test_scan_bola_no_credentials(mock_base_url):
    findings = scan_bola(mock_base_url, {})
    assert findings == []

def test_scan_bola_invalid_url(mock_credentials):
    findings = scan_bola("http://invalid-url", mock_credentials)
    assert findings == []

def test_scan_bola_response_structure(mock_base_url, mock_credentials):
    findings = scan_bola(mock_base_url, mock_credentials)
    if findings:
        assert "id" in findings[0]
        assert "title" in findings[0]
        assert "type" in findings[0]
        assert "severity" in findings[0]
        assert "confidence" in findings[0]
        assert "endpoint" in findings[0]
        assert "timestamp" in findings[0]