from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.auth_service import AuthService
from app.services.scanner_service import ScannerService
from app.services.report_service import ReportService

def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)

def get_scanner_service(db: Session = Depends(get_db)) -> ScannerService:
    return ScannerService(db)

def get_report_service(db: Session = Depends(get_db)) -> ReportService:
    return ReportService(db)