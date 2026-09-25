from datetime import datetime
from typing import List, Dict, Any

class ReportService:
    def __init__(self):
        self.reports = []

    def generate_report(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "findings": findings,
            "summary": self.summarize_findings(findings),
        }
        self.reports.append(report)
        return report

    def summarize_findings(self, findings: List[Dict[str, Any]]) -> Dict[str, Any]:
        summary = {
            "total_findings": len(findings),
            "critical": sum(1 for finding in findings if finding["severity"] == "CRITICAL"),
            "high": sum(1 for finding in findings if finding["severity"] == "HIGH"),
            "medium": sum(1 for finding in findings if finding["severity"] == "MEDIUM"),
            "low": sum(1 for finding in findings if finding["severity"] == "LOW"),
        }
        return summary

    def get_reports(self) -> List[Dict[str, Any]]:
        return self.reports

    def clear_reports(self) -> None:
        self.reports = []