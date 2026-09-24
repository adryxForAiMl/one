from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.scanner.bola_scanner import scan_bola


app = FastAPI(
    title="SentinelAPI",
    description="Zero-Trust API Vulnerability Scanner",
    version="0.3.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "name": "SentinelAPI",
        "status": "online",
        "version": "0.3.0"
    }


@app.post("/scan")
def scan():
    credentials = {
        "User A": "token-user-a",
        "User B": "token-user-b"
    }

    target = "http://127.0.0.1:8000"

    findings = scan_bola(
        target,
        credentials
    )

    severity_counts = {
        "CRITICAL": 0,
        "HIGH": 0,
        "MEDIUM": 0,
        "LOW": 0
    }

    for finding in findings:
        severity = finding.get("severity")

        if severity in severity_counts:
            severity_counts[severity] += 1

    return {
        "scan_id": "scan-001",
        "status": "completed",
        "target": "Local Sandbox API",

        "summary": {
            "vulnerabilities": len(findings),
            "critical": severity_counts["CRITICAL"],
            "high": severity_counts["HIGH"],
            "medium": severity_counts["MEDIUM"],
            "low": severity_counts["LOW"]
        },

        "findings": findings
    }
