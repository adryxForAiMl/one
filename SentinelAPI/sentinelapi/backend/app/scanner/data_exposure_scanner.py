from __future__ import annotations

import json
from typing import Any, Dict, List

class DataExposureScanner:
    """Scanner for detecting excessive data exposure in API responses."""

    SENSITIVE_KEY_PATTERNS = {
        "password",
        "secret",
        "token",
        "api_key",
        "apikey",
        "access_token",
        "private_key",
        "ssn",
        "credit_card",
        "card_number",
        "cvv",
        "pin",
        "tax_id",
        "phone",
        "email",
        "salary",
    }

    def __init__(self, api_spec: Dict[str, Any]):
        self.api_spec = api_spec

    def scan(self, response_data: Any) -> List[str]:
        """Scan the response data for excessive data exposure."""
        exposed_fields = self.detect_sensitive_fields(response_data)
        return exposed_fields

    def detect_sensitive_fields(self, data: Any) -> List[str]:
        """Inspect returned payload keys for excessive data exposure."""
        exposed: List[str] = []
        if isinstance(data, dict):
            for k, v in data.items():
                key_lower = str(k).lower()
                if any(p in key_lower for p in self.SENSITIVE_KEY_PATTERNS):
                    exposed.append(str(k))
                if isinstance(v, (dict, list)):
                    exposed.extend(self.detect_sensitive_fields(v))
        elif isinstance(data, list):
            for item in data:
                exposed.extend(self.detect_sensitive_fields(item))
        return sorted(set(exposed))

    def generate_report(self, findings: List[str]) -> str:
        """Generate a report of the findings."""
        report = {
            "findings": findings,
            "total_exposed_fields": len(findings),
        }
        return json.dumps(report, indent=2)