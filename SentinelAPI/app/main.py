from fastapi import FastAPI
from app.scanner.bola_scanner import scan_bola

app = FastAPI(
    title="SentinelAPI",
    description="Zero-Trust API Vulnerability Scanner",
    version="0.1.0"
)


@app.get("/")
def home():
    return {
        "name": "SentinelAPI",
        "status": "online",
        "version": "0.1.0"
    }


@app.post("/scan")
def scan():
    findings = scan_bola("http://127.0.0.1:8000")

    return {
        "scanner": "SentinelAPI",
        "status": "completed",
        "findings_count": len(findings),
        "findings": findings
    }