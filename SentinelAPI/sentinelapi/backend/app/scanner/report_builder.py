from typing import List, Dict, Any

def build_report(findings: List[Dict[str, Any]]) -> Dict[str, Any]:
    report = {
        "total_findings": len(findings),
        "findings": []
    }

    for finding in findings:
        report["findings"].append({
            "id": finding["id"],
            "title": finding["title"],
            "severity": finding["severity"],
            "timestamp": finding["timestamp"],
            "endpoint": finding["endpoint"],
            "attacker": finding["attacker"],
            "resource_owner": finding["resource_owner"],
            "object_id": finding["object_id"],
            "status_code": finding["status_code"],
            "description": finding["description"],
            "impact": finding["impact"],
            "remediation": finding["remediation"],
            "evidence": finding["evidence"],
            "security_reasoning": finding["security_reasoning"],
        })

    return report

def generate_summary(report: Dict[str, Any]) -> str:
    summary_lines = [
        f"Total Findings: {report['total_findings']}",
        "Findings Summary:"
    ]

    for finding in report["findings"]:
        summary_lines.append(f"- {finding['title']} (Severity: {finding['severity']})")

    return "\n".join(summary_lines)

def save_report_to_file(report: Dict[str, Any], file_path: str) -> None:
    import json

    with open(file_path, 'w') as f:
        json.dump(report, f, indent=4)

def load_findings_from_file(file_path: str) -> List[Dict[str, Any]]:
    import json

    with open(file_path, 'r') as f:
        return json.load(f)