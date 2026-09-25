from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Finding(BaseModel):
    id: str
    title: str
    type: str
    severity: str
    confidence: float
    confidence_label: str
    category: str
    cwe: str
    cwe_title: str
    owasp: str
    endpoint: str
    method: str
    attacker: str
    resource_owner: str
    object_id: str
    status_code: int
    status: str
    timestamp: datetime
    evidence: dict
    impact: str
    remediation: str
    description: str
    security_reasoning: List[str]

class Report(BaseModel):
    scan_id: str
    findings: List[Finding]
    generated_at: datetime
    total_findings: int
    critical_findings: int
    high_findings: int
    medium_findings: int
    low_findings: int
    info_findings: int
    summary: str