from datetime import datetime
from typing import List, Dict, Any

from app.models.scan import Scan
from app.models.finding import Finding
from app.scanner.bola_scanner import scan_bola
from app.schemas.scan import ScanCreate
from app.schemas.finding import FindingCreate


class ScanService:
    def __init__(self):
        self.scans: List[Scan] = []
        self.findings: List[Finding] = []

    def create_scan(self, scan_data: ScanCreate) -> Scan:
        scan = Scan(
            id=len(self.scans) + 1,
            name=scan_data.name,
            target_url=scan_data.target_url,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        self.scans.append(scan)
        return scan

    def execute_scan(self, scan: Scan, credentials: Dict[str, str], auth_type: str = "authorization", auth_header: str = "Authorization") -> List[Finding]:
        findings = scan_bola(scan.target_url, credentials, auth_type, auth_header)
        self.findings.extend(findings)
        return findings

    def get_scan_results(self, scan_id: int) -> List[Finding]:
        return [finding for finding in self.findings if finding.scan_id == scan_id]