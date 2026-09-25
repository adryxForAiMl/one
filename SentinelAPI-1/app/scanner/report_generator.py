from typing import List, Dict, Any

def generate_report(findings: List[Dict[str, Any]]) -> str:
    """Generate a report from scan findings."""
    report_lines = []
    report_lines.append("## Vulnerability Report\n")
    
    for finding in findings:
        report_lines.append(f"### Finding ID: {finding['id']}")
        report_lines.append(f"**Title:** {finding['title']}")
        report_lines.append(f"**Severity:** {finding['severity']}")
        report_lines.append(f"**Endpoint:** {finding['endpoint']}")
        report_lines.append(f"**Attacker:** {finding['attacker']}")
        report_lines.append(f"**Resource Owner:** {finding['resource_owner']}")
        report_lines.append(f"**Object ID:** {finding['object_id']}")
        report_lines.append(f"**Status Code:** {finding['status_code']}")
        report_lines.append(f"**Impact:** {finding['impact']}")
        report_lines.append(f"**Description:** {finding['description']}")
        report_lines.append("\n---\n")
    
    return "\n".join(report_lines)

def save_report(report: str, file_path: str) -> None:
    """Save the generated report to a file."""
    with open(file_path, 'w') as report_file:
        report_file.write(report)

def generate_and_save_report(findings: List[Dict[str, Any]], file_path: str) -> None:
    """Generate a report from findings and save it to the specified file path."""
    report = generate_report(findings)
    save_report(report, file_path)