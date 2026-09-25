from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ScanCreate(BaseModel):
    target_url: str
    scan_type: str
    credentials: Optional[dict[str, str]] = None

class Scan(BaseModel):
    id: int
    target_url: str
    scan_type: str
    status: str
    created_at: datetime
    updated_at: datetime
    findings: List[int]  # List of finding IDs associated with this scan

class ScanUpdate(BaseModel):
    status: Optional[str] = None
    findings: Optional[List[int]] = None