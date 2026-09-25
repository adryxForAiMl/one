from pydantic import BaseModel
from typing import List, Optional

class Evidence(BaseModel):
    finding_id: str
    timestamp: str
    request: dict
    response: dict
    response_metadata: dict
    response_fingerprint: str
    attacker_collection: Optional[dict]
    resource_owner_collection: Optional[dict]
    sensitive_fields_exposed: List[str]

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
    endpoint_template: str
    method: str
    attacker: str
    resource_owner: str
    object_id: str
    status_code: int
    status: str
    timestamp: str
    verification: dict
    evidence: Evidence
    impact: str
    remediation: str
    developer_remediation: dict
    description: str
    security_reasoning: List[str]