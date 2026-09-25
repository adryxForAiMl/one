"""
KAVACH Core Main Application.
Zero-Trust API Security and Authorization Intelligence Platform.
Provides Target Preflight, Netra Discovery, Deterministic Raksha BOLA Testing,
Drishti Local ML Risk Scoring, Trace Attack Graph Synthesis, and Security Posture Scorecards.
"""

from __future__ import annotations

import csv
import io
import json
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.intelligence.risk_engine import calculate_intelligent_risk
from app.scanner.bola_scanner import find_object_endpoints, scan_bola
from app.scanner.openapi_parser import OpenAPIParser
from app.scanner.target_preflight import (
    OPENAPI_CANDIDATE_PATHS,
    normalize_target_url,
    run_target_preflight,
)


app = FastAPI(
    title="KAVACH Security Engine",
    description="Zero-Trust API Security and Authorization Intelligence Engine",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# In-memory scan storage for audit trails and historical inspection
SCAN_HISTORY: dict[str, dict[str, Any]] = {}


class AuthenticationConfig(BaseModel):
    type: str = "none"
    token: str | None = None
    api_key: str | None = None
    header: str | None = None


class AuthenticationProfile(BaseModel):
    name: str
    type: str = "bearer"
    token: str | None = None
    api_key: str | None = None
    header: str | None = None


class PreflightRequest(BaseModel):
    target_url: str | None = None
    target: str | None = None
    url: str | None = None

    @property
    def resolved_url(self) -> str:
        val = self.target_url or self.target or self.url
        if not val or not str(val).strip():
            raise HTTPException(
                status_code=400,
                detail="Target API URL cannot be empty.",
            )
        return str(val).strip()


class ScanRequest(BaseModel):
    target_url: str | None = None
    target: str | None = None
    url: str | None = None
    authentication_profiles: list[AuthenticationProfile] = Field(default_factory=list)
    authentication: AuthenticationConfig | None = None
    user_a_token: str | None = None
    user_b_token: str | None = None
    auth_header: str | None = None

    @property
    def resolved_target_url(self) -> str:
        val = self.target_url or self.target or self.url
        if not val or not str(val).strip():
            raise HTTPException(
                status_code=400,
                detail="Target API URL cannot be empty.",
            )
        return str(val).strip()


@app.get("/")
def home():
    return {
        "name": "KAVACH",
        "title": "KAVACH — Zero-Trust API Security Platform",
        "tagline": "Zero-Trust API Security",
        "mission": "Discover. Verify. Explain. Protect.",
        "status": "online",
        "version": "1.0.0",
        "modules": {
            "core": "KAVACH Core",
            "discovery": "KAVACH Netra",
            "intelligence": "KAVACH Drishti",
            "authorization": "KAVACH Kavach-Auth",
            "bola": "KAVACH Raksha",
            "trace": "KAVACH Trace",
            "evidence": "KAVACH Pramaan",
            "remediation": "KAVACH Suraksha",
            "reports": "KAVACH Dastaavez",
            "lab": "KAVACH Lab",
        },
        "capabilities": [
            "target-preflight",
            "netra-openapi-discovery",
            "kavach-auth-identity-mapping",
            "raksha-deterministic-bola-testing",
            "pramaan-response-fingerprinting",
            "drishti-local-ml-risk-scoring",
            "trace-attack-graph-reconstruction",
            "suraksha-developer-remediation",
            "security-scorecard",
            "dastaavez-audit-reporting",
        ],
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "KAVACH Security Engine",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/validate-target")
@app.post("/preflight")
def preflight(request: PreflightRequest):
    """
    Execute non-destructive preflight validation on a target API.
    Validates URL, connectivity, latency, OpenAPI discovery, and scan readiness.
    """
    target = request.resolved_url
    result = run_target_preflight(target)
    return result


def normalize_target(target_url: str) -> str:
    try:
        return normalize_target_url(target_url)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


def discover_openapi_endpoints(
    target: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Discover, ingest, and normalize OpenAPI/Swagger endpoints."""
    spec: dict[str, Any] | None = None
    found_url: str | None = None

    with httpx.Client(timeout=10.0, follow_redirects=True) as client:
        for path in OPENAPI_CANDIDATE_PATHS:
            try:
                res = client.get(f"{target}{path}")
                if res.status_code == 200:
                    spec_data = res.json()
                    if isinstance(spec_data, dict) and ("paths" in spec_data or "openapi" in spec_data or "swagger" in spec_data):
                        spec = spec_data
                        found_url = f"{target}{path}"
                        break
            except Exception:
                continue

    if not spec:
        raise HTTPException(
            status_code=422,
            detail=(
                "Target API does not expose a discoverable OpenAPI or Swagger specification. "
                "OpenAPI discovery is required for zero-trust authorization mapping."
            ),
        )

    try:
        parser = OpenAPIParser(spec)
        endpoints = [ep.to_dict() for ep in parser.endpoints]
    except Exception:
        # Fallback to direct extraction
        raw_paths = spec.get("paths", {})
        endpoints = []
        for path, methods in raw_paths.items():
            if isinstance(methods, dict):
                for method in methods:
                    endpoints.append({
                        "path": path,
                        "method": method.upper(),
                        "category": "object" if "{" in path else "collection",
                        "authorization_tested": "{" in path and method.upper() == "GET",
                    })

    return spec, endpoints


def build_endpoint_results(
    endpoints: list[dict[str, Any]],
    findings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    severity_order = {
        "CRITICAL": 4,
        "HIGH": 3,
        "MEDIUM": 2,
        "LOW": 1,
    }

    endpoint_state: dict[tuple[str, str], dict[str, Any]] = {
        (ep["path"], ep["method"]): {
            "finding_count": 0,
            "severity": None,
        }
        for ep in endpoints
    }

    def matches_endpoint(endpoint: dict[str, Any], finding: dict[str, Any]) -> bool:
        ep_method = str(endpoint.get("method", "GET")).upper()
        finding_method = str(finding.get("method", "GET")).upper()
        if ep_method != finding_method:
            return False

        template = str(endpoint.get("path", ""))
        concrete = str(finding.get("endpoint", ""))
        if template == concrete:
            return True

        template_parts = [p for p in template.split("/") if p]
        concrete_parts = [p for p in concrete.split("/") if p]
        if len(template_parts) != len(concrete_parts):
            return False

        for t_part, c_part in zip(template_parts, concrete_parts):
            if t_part.startswith("{") and t_part.endswith("}"):
                continue
            if t_part != c_part:
                return False
        return True

    for finding in findings:
        matched = next((ep for ep in endpoints if matches_endpoint(ep, finding)), None)
        if not matched:
            continue

        key = (matched["path"], matched["method"])
        state = endpoint_state[key]
        state["finding_count"] += 1
        sev = str(finding.get("severity", "LOW")).upper()
        cur = state["severity"]
        if cur is None or severity_order.get(sev, 0) > severity_order.get(cur, 0):
            state["severity"] = sev

    results = []
    for ep in endpoints:
        key = (ep["path"], ep["method"])
        state = endpoint_state.get(key, {"finding_count": 0, "severity": None})
        count = state["finding_count"]
        if count > 0:
            status = "vulnerable"
        elif ep.get("authorization_tested", False):
            status = "tested"
        else:
            status = "discovered"

        results.append({
            **ep,
            "finding_count": count,
            "severity": state["severity"],
            "status": status,
        })

    return results


def select_authentication(
    request: ScanRequest,
    target: str,
) -> tuple[dict[str, str], str, str]:
    is_sandbox = target in ("http://127.0.0.1:8000", "http://localhost:8000")

    if is_sandbox and not request.authentication_profiles and not (request.user_a_token and request.user_b_token):
        return (
            {
                "User A": "token-user-a",
                "User B": "token-user-b",
            },
            "authorization",
            "Authorization",
        )

    if request.user_a_token and request.user_b_token:
        return (
            {
                "User A": request.user_a_token,
                "User B": request.user_b_token,
            },
            "authorization" if is_sandbox else "bearer",
            request.auth_header or "Authorization",
        )

    credentials: dict[str, str] = {}
    scanner_auth_type = "authorization" if is_sandbox else "bearer"
    scanner_auth_header = "Authorization"

    if request.authentication_profiles:
        for profile in request.authentication_profiles:
            token_val = profile.token if profile.type == "bearer" else profile.api_key
            if token_val:
                credentials[profile.name] = token_val

        first_profile = request.authentication_profiles[0]
        if first_profile.type == "api-key":
            scanner_auth_type = "api-key"
            scanner_auth_header = first_profile.header or "X-API-Key"
        elif first_profile.type == "bearer":
            scanner_auth_type = "authorization" if is_sandbox else "bearer"
            scanner_auth_header = "Authorization"

        return credentials, scanner_auth_type, scanner_auth_header

    if request.authentication:
        if request.authentication.type == "bearer" and request.authentication.token:
            credentials["API User"] = request.authentication.token
            scanner_auth_type = "authorization" if is_sandbox else "bearer"
            scanner_auth_header = "Authorization"
        elif request.authentication.type == "api-key" and request.authentication.api_key:
            credentials["API User"] = request.authentication.api_key
            scanner_auth_type = "api-key"
            scanner_auth_header = request.authentication.header or "X-API-Key"

    return credentials, scanner_auth_type, scanner_auth_header


def build_attack_graph_data(
    findings: list[dict[str, Any]],
    endpoints: list[dict[str, Any]],
) -> dict[str, Any]:
    """Synthesize interactive React Flow graph models for attack path and surface topology."""
    paths = []
    for f in findings:
        attacker = f.get("attacker", "Attacker")
        victim = f.get("resource_owner", "Victim")
        obj_id = f.get("object_id", "Unknown")
        endpoint = f.get("endpoint", "")
        method = f.get("method", "GET")
        f_id = f.get("id", "BOLA-001")

        nodes = [
            {
                "id": "attacker",
                "type": "security",
                "position": {"x": 40, "y": 180},
                "data": {
                    "label": attacker,
                    "subtitle": "Authenticated Caller",
                    "variant": "attacker",
                },
            },
            {
                "id": "credential",
                "type": "security",
                "position": {"x": 280, "y": 180},
                "data": {
                    "label": "Identity Token",
                    "subtitle": "Valid Session Scope",
                    "variant": "auth",
                },
            },
            {
                "id": "api",
                "type": "security",
                "position": {"x": 520, "y": 180},
                "data": {
                    "label": "API Resource",
                    "subtitle": f"{method} {endpoint}",
                    "variant": "api",
                },
            },
            {
                "id": "object",
                "type": "security",
                "position": {"x": 760, "y": 180},
                "data": {
                    "label": f"Object #{obj_id}",
                    "subtitle": "Protected Record",
                    "variant": "object",
                },
            },
            {
                "id": "owner",
                "type": "security",
                "position": {"x": 1000, "y": 180},
                "data": {
                    "label": victim,
                    "subtitle": "Resource Owner",
                    "variant": "owner",
                },
            },
            {
                "id": "breach",
                "type": "security",
                "position": {"x": 760, "y": 320},
                "data": {
                    "label": "HTTP 200 Leaked",
                    "subtitle": "BOLA Confirmed",
                    "variant": "violation",
                },
            },
        ]

        edges = [
            {
                "id": f"{f_id}-e1",
                "source": "attacker",
                "target": "credential",
                "label": "Assumes Identity",
                "style": {"stroke": "#ef4444", "strokeWidth": 2},
                "animated": True,
            },
            {
                "id": f"{f_id}-e2",
                "source": "credential",
                "target": "api",
                "label": "Sends Token",
                "style": {"stroke": "#ef4444", "strokeWidth": 2},
                "animated": True,
            },
            {
                "id": f"{f_id}-e3",
                "source": "api",
                "target": "object",
                "label": f"Requests #{obj_id}",
                "style": {"stroke": "#f59e0b", "strokeWidth": 2},
                "animated": True,
            },
            {
                "id": f"{f_id}-e4",
                "source": "object",
                "target": "owner",
                "label": "Owned By",
                "style": {"stroke": "#22c55e", "strokeWidth": 2},
            },
            {
                "id": f"{f_id}-e5",
                "source": "object",
                "target": "breach",
                "label": "Unauthorized Disclosure",
                "style": {"stroke": "#dc2626", "strokeWidth": 2, "strokeDasharray": "5,5"},
                "animated": True,
            },
        ]

        paths.append({
            "finding_id": f_id,
            "title": f"{attacker} → {victim} (Object #{obj_id})",
            "nodes": nodes,
            "edges": edges,
        })

    return {
        "paths": paths,
        "total_paths": len(paths),
    }


@app.post("/scans")
@app.post("/scan")
def scan(request: ScanRequest):
    started_at = datetime.now(timezone.utc)
    target = normalize_target(request.resolved_target_url)

    spec, discovered_endpoints = discover_openapi_endpoints(target)
    credentials, scanner_auth_type, scanner_auth_header = select_authentication(request, target)

    findings = scan_bola(
        target,
        credentials,
        auth_type=scanner_auth_type,
        auth_header=scanner_auth_header,
    )

    severity_counts = {
        "CRITICAL": 0,
        "HIGH": 0,
        "MEDIUM": 0,
        "LOW": 0,
    }
    for f in findings:
        sev = f.get("severity", "LOW")
        if sev in severity_counts:
            severity_counts[sev] += 1

    endpoint_results = build_endpoint_results(discovered_endpoints, findings)
    tested_endpoints = sum(1 for ep in endpoint_results if ep.get("authorization_tested"))
    vulnerable_endpoints = sum(1 for ep in endpoint_results if ep.get("finding_count", 0) > 0)

    intelligent_risk = calculate_intelligent_risk(findings, endpoint_results)
    enriched_findings = intelligent_risk.get("findings", findings)
    scorecard = intelligent_risk.get("scorecard", {})
    attack_graph = build_attack_graph_data(enriched_findings, endpoint_results)

    openapi_version = spec.get("openapi") or spec.get("swagger") or "3.0.0"
    target_name = (
        "Authorized Local Security Demo"
        if target in ("http://127.0.0.1:8000", "http://localhost:8000")
        else target
    )

    scan_id = f"scan-{started_at.strftime('%Y%m%d%H%M%S%f')[:-3]}"

    scan_response = {
        "scan_id": scan_id,
        "status": "completed",
        "target": target_name,
        "target_url": target,
        "scan_metadata": {
            "scanner": "KAVACH Zero-Trust Security Engine",
            "tagline": "Zero-Trust API Security",
            "platform": "KAVACH",
            "core_engine": "KAVACH Core",
            "started_at": started_at.isoformat(),
            "authentication_profiles": len(credentials),
            "authorization_testing": len(credentials) >= 2,
            "openapi_discovery": True,
            "openapi_version": openapi_version,
            "discovered_endpoints": len(endpoint_results),
            "tested_endpoints": tested_endpoints,
            "vulnerable_endpoints": vulnerable_endpoints,
            "intelligence_engine": "drishti-ml-enabled",
        },
        "discovery": {
            "openapi_url": f"{target}/openapi.json",
            "openapi_version": openapi_version,
            "endpoint_count": len(endpoint_results),
            "object_endpoint_count": sum(1 for ep in endpoint_results if ep.get("category") == "object"),
            "collection_endpoint_count": sum(1 for ep in endpoint_results if ep.get("category") == "collection"),
        },
        "endpoints": endpoint_results,
        "risk": {
            "score": intelligent_risk["score"],
            "level": intelligent_risk["level"],
            "base_score": intelligent_risk["base_score"],
            "confidence": intelligent_risk["confidence"],
            "confidence_label": intelligent_risk["confidence_label"],
            "anomaly_score": intelligent_risk["anomaly_score"],
            "anomaly_label": intelligent_risk["anomaly_label"],
            "exposure_score": intelligent_risk["exposure_score"],
            "why_explanation": intelligent_risk.get("why_explanation"),
            "scorecard": scorecard,
            "ai_summary": intelligent_risk["ai_summary"],
            "ml_engine": intelligent_risk["ml_engine"],
        },
        "summary": {
            "vulnerabilities": len(enriched_findings),
            "critical": severity_counts["CRITICAL"],
            "high": severity_counts["HIGH"],
            "medium": severity_counts["MEDIUM"],
            "low": severity_counts["LOW"],
        },
        "findings": enriched_findings,
        "attack_graph": attack_graph,
    }

    # Save to scan history (capped at 50)
    SCAN_HISTORY[scan_id] = scan_response
    if len(SCAN_HISTORY) > 50:
        oldest_key = next(iter(SCAN_HISTORY))
        del SCAN_HISTORY[oldest_key]

    return scan_response


@app.get("/scans")
def list_scans():
    """Return past scan summaries from session history."""
    items = []
    for s_id, s_data in reversed(list(SCAN_HISTORY.items())):
        items.append({
            "scan_id": s_id,
            "target": s_data.get("target"),
            "target_url": s_data.get("target_url"),
            "started_at": s_data.get("scan_metadata", {}).get("started_at"),
            "risk_score": s_data.get("risk", {}).get("score", 0),
            "risk_level": s_data.get("risk", {}).get("level", "SECURE"),
            "vulnerabilities": s_data.get("summary", {}).get("vulnerabilities", 0),
            "critical": s_data.get("summary", {}).get("critical", 0),
            "endpoint_count": s_data.get("discovery", {}).get("endpoint_count", 0),
            "status": s_data.get("status", "completed"),
        })
    return items


@app.get("/scans/{scan_id}")
def get_scan(scan_id: str):
    """Retrieve full scan result by ID."""
    if scan_id not in SCAN_HISTORY:
        raise HTTPException(status_code=404, detail=f"Scan ID '{scan_id}' not found.")
    return SCAN_HISTORY[scan_id]


@app.get("/scans/{scan_id}/export/json")
def export_scan_json(scan_id: str):
    """Export scan as downloadable JSON."""
    if scan_id not in SCAN_HISTORY:
        raise HTTPException(status_code=404, detail="Scan not found.")
    data = json.dumps(SCAN_HISTORY[scan_id], indent=2)
    return Response(
        content=data,
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={scan_id}-report.json"},
    )


@app.get("/scans/{scan_id}/export/csv")
def export_scan_csv(scan_id: str):
    """Export findings from scan as CSV."""
    if scan_id not in SCAN_HISTORY:
        raise HTTPException(status_code=404, detail="Scan not found.")
    findings = SCAN_HISTORY[scan_id].get("findings", [])

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Finding ID",
        "Severity",
        "Category",
        "CWE",
        "OWASP",
        "Method",
        "Endpoint",
        "Attacker",
        "Resource Owner",
        "Object ID",
        "HTTP Status",
        "Confidence",
        "Anomaly Score",
        "Impact",
    ])
    for f in findings:
        writer.writerow([
            f.get("id"),
            f.get("severity"),
            f.get("category"),
            f.get("cwe"),
            f.get("owasp"),
            f.get("method"),
            f.get("endpoint"),
            f.get("attacker"),
            f.get("resource_owner"),
            f.get("object_id"),
            f.get("status_code"),
            f.get("confidence"),
            f.get("anomaly_score"),
            f.get("impact"),
        ])
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={scan_id}-findings.csv"},
    )
