from fastapi import APIRouter, HTTPException
from app.schemas.report import ReportCreate, ReportResponse
from app.services.report_service import ReportService

router = APIRouter()
report_service = ReportService()

@router.post("/", response_model=ReportResponse)
async def create_report(report: ReportCreate):
    created_report = await report_service.create_report(report)
    if not created_report:
        raise HTTPException(status_code=400, detail="Failed to create report")
    return created_report

@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(report_id: int):
    report = await report_service.get_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

@router.get("/", response_model=list[ReportResponse])
async def list_reports():
    reports = await report_service.list_reports()
    return reports