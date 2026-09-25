from typing import Dict, Any

# Define types used in the scanner

class ScanResult:
    def __init__(self, id: str, title: str, severity: str, description: str, evidence: Dict[str, Any]):
        self.id = id
        self.title = title
        self.severity = severity
        self.description = description
        self.evidence = evidence

class Finding:
    def __init__(self, finding_id: str, resource_owner: str, object_id: str, status_code: int, status: str):
        self.finding_id = finding_id
        self.resource_owner = resource_owner
        self.object_id = object_id
        self.status_code = status_code
        self.status = status

class UserCredential:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password

class APIResponse:
    def __init__(self, status_code: int, body: Any):
        self.status_code = status_code
        self.body = body

class EndpointInfo:
    def __init__(self, object_path: str, collection_path: str, parameter: str):
        self.object_path = object_path
        self.collection_path = collection_path
        self.parameter = parameter