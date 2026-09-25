from fastapi import FastAPI
from app.api.routes import auth, scans, reports, health

app = FastAPI(title="SentinelAPI: Zero-Trust API Vulnerability Scanner")

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(scans.router, prefix="/scans", tags=["scans"])
app.include_router(reports.router, prefix="/reports", tags=["reports"])
app.include_router(health.router, prefix="/health", tags=["health"])

@app.get("/")
async def root():
    return {"message": "Welcome to the SentinelAPI: Zero-Trust API Vulnerability Scanner"}