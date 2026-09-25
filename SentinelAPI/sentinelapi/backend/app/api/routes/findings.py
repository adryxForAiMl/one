from fastapi import APIRouter, HTTPException, Depends
from app.schemas.finding import FindingCreate, Finding
from app.services.finding_service import FindingService

router = APIRouter()
finding_service = FindingService()

@router.post("/", response_model=Finding)
async def create_finding(finding: FindingCreate):
    created_finding = await finding_service.create_finding(finding)
    if not created_finding:
        raise HTTPException(status_code=400, detail="Failed to create finding")
    return created_finding

@router.get("/{finding_id}", response_model=Finding)
async def get_finding(finding_id: int):
    finding = await finding_service.get_finding(finding_id)
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    return finding

@router.get("/", response_model=list[Finding])
async def list_findings(skip: int = 0, limit: int = 10):
    findings = await finding_service.list_findings(skip=skip, limit=limit)
    return findings

@router.delete("/{finding_id}", response_model=dict)
async def delete_finding(finding_id: int):
    success = await finding_service.delete_finding(finding_id)
    if not success:
        raise HTTPException(status_code=404, detail="Finding not found")
    return {"detail": "Finding deleted successfully"}