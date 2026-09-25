from __future__ import annotations

import httpx
from datetime import datetime
from typing import Any, Dict, List

DEFAULT_TIMEOUT = 10.0

class RateLimitScanner:
    def __init__(self, base_url: str, endpoints: List[str]):
        self.base_url = base_url.rstrip('/')
        self.endpoints = endpoints

    def scan(self, headers: Dict[str, str]) -> List[Dict[str, Any]]:
        findings = []
        with httpx.Client(timeout=DEFAULT_TIMEOUT) as client:
            for endpoint in self.endpoints:
                response = self._test_rate_limit(client, endpoint, headers)
                if response:
                    findings.append(response)
        return findings

    def _test_rate_limit(self, client: httpx.Client, endpoint: str, headers: Dict[str, str]) -> Dict[str, Any] | None:
        # Send multiple requests to the endpoint to test rate limiting
        responses = []
        for _ in range(5):  # Adjust the number of requests as needed
            response = client.get(f"{self.base_url}{endpoint}", headers=headers)
            responses.append(response)

        # Analyze responses to determine if rate limiting is enforced
        if all(res.status_code == 200 for res in responses):
            return {
                "endpoint": endpoint,
                "status": "no rate limit",
                "timestamp": datetime.now().isoformat(),
                "responses": [res.json() for res in responses],
            }
        elif any(res.status_code == 429 for res in responses):
            return {
                "endpoint": endpoint,
                "status": "rate limit enforced",
                "timestamp": datetime.now().isoformat(),
                "responses": [res.json() for res in responses],
            }
        return None
