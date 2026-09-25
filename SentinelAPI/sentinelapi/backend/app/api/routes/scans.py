from fastapi import APIRouter, HTTPException, Depends
from app.schemas.scan import ScanCreate, ScanResponse
from app.services.scan_service import ScanService

router = APIRouter()
scan_service = ScanService()

@router.post("/", response_model=ScanResponse)
async def create_scan(scan: ScanCreate):
    try:
        return await scan_service.create_scan(scan)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{scan_id}", response_model=ScanResponse)
async def get_scan(scan_id: int):
    scan = await scan_service.get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan

@router.get("/")
async def list_scans(skip: int = 0, limit: int = 10):
    return await scan_service.list_scans(skip=skip, limit=limit)