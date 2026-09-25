from typing import List, Dict, Any

class FindingService:
    def __init__(self):
        self.findings = []

    def add_finding(self, finding: Dict[str, Any]) -> None:
        """Add a new finding to the service."""
        self.findings.append(finding)

    def get_findings(self) -> List[Dict[str, Any]]:
        """Retrieve all findings."""
        return self.findings

    def get_finding_by_id(self, finding_id: str) -> Dict[str, Any]:
        """Retrieve a finding by its ID."""
        for finding in self.findings:
            if finding['id'] == finding_id:
                return finding
        return {}

    def remove_finding(self, finding_id: str) -> bool:
        """Remove a finding by its ID."""
        for i, finding in enumerate(self.findings):
            if finding['id'] == finding_id:
                del self.findings[i]
                return True
        return False

    def clear_findings(self) -> None:
        """Clear all findings."""
        self.findings.clear()