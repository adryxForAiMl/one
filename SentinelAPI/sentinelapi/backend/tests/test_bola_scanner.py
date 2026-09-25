from app.scanner.bola_scanner import scan_bola

def test_scan_bola():
    base_url = "http://localhost:8000"  # Replace with your API base URL
    credentials = {
        "user1": "token1",
        "user2": "token2",
    }
    
    findings = scan_bola(base_url, credentials)

    assert isinstance(findings, list)
    assert all(isinstance(finding, dict) for finding in findings)
    assert all("id" in finding for finding in findings)
    assert all("title" in finding for finding in findings)
    assert all("severity" in finding for finding in findings)