from pydantic import BaseModel
from typing import List, Optional

class ScanRequest(BaseModel):
    url: str
    credentials: dict
    auth_type: Optional[str] = "authorization"
    auth_header: Optional[str] = "Authorization"

class ScanResult(BaseModel):
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
    timestamp: str
    verification: dict
    evidence: dict
    impact: str
    remediation: str
    developer_remediation: dict
    description: str
    security_reasoning: List[str]

class ScanReport(BaseModel):
    findings: List[ScanResult]