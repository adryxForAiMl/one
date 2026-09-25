from fastapi import APIRouter, HTTPException, Depends
from app.schemas.scan import ScanCreate, ScanResponse
from app.services.scanner_service import ScannerService
from app.api.deps import get_scanner_service

router = APIRouter()

@router.post("/", response_model=ScanResponse)
async def create_scan(scan: ScanCreate, scanner_service: ScannerService = Depends(get_scanner_service)):
    """
    Create a new scan.
    """
    return await scanner_service.create_scan(scan)

@router.get("/{scan_id}", response_model=ScanResponse)
async def get_scan(scan_id: int, scanner_service: ScannerService = Depends(get_scanner_service)):
    """
    Retrieve a scan by its ID.
    """
    scan = await scanner_service.get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return scan

@router.get("/")
async def list_scans(scanner_service: ScannerService = Depends(get_scanner_service)):
    """
    List all scans.
    """
    return await scanner_service.list_scans()