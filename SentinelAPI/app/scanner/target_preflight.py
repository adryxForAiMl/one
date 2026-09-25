"""
Target Preflight Engine for KAVACH.
Validates reachability, HTTP connectivity, latency, OpenAPI discovery,
and evaluates scan readiness with structured security checks.
"""

from __future__ import annotations

import time
import urllib.parse
from typing import Any

import httpx

from app.scanner.openapi_parser import OpenAPIParser


OPENAPI_CANDIDATE_PATHS = [
    "/openapi.json",
    "/swagger.json",
    "/api/openapi.json",
    "/v1/openapi.json",
    "/api/v1/openapi.json",
    "/v2/openapi.json",
    "/docs/openapi.json",
]


class PreflightCheckResult:
    def __init__(
        self,
        name: str,
        label: str,
        status: str,  # "pass" | "warn" | "fail"
        detail: str,
    ):
        self.name = name
        self.label = label
        self.status = status
        self.detail = detail

    def to_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "label": self.label,
            "status": self.status,
            "detail": self.detail,
        }


def normalize_target_url(raw_url: str) -> str:
    """Normalize and validate target URL."""
    url = raw_url.strip()
    if not url:
        raise ValueError("Target API URL cannot be empty.")

    if not url.startswith(("http://", "https://")):
        url = f"http://{url}"

    parsed = urllib.parse.urlparse(url)
    if not parsed.netloc:
        raise ValueError("Invalid target API URL. Hostname or IP is missing.")

    # Reconstruct normalized URL without trailing slash
    normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")
    return normalized


def run_target_preflight(target_url: str, timeout: float = 6.0) -> dict[str, Any]:
    """Execute complete target preflight inspection."""
    checklist: list[PreflightCheckResult] = []

    # 1. URL Format Validation
    try:
        normalized = normalize_target_url(target_url)
        checklist.append(
            PreflightCheckResult(
                name="url_format",
                label="URL FORMAT",
                status="pass",
                detail=f"Normalized target to {normalized}",
            )
        )
    except ValueError as exc:
        checklist.append(
            PreflightCheckResult(
                name="url_format",
                label="URL FORMAT",
                status="fail",
                detail=str(exc),
            )
        )
        return {
            "status": "SCAN_NOT_READY",
            "state_code": "INVALID_URL",
            "target_url": target_url,
            "reachable": False,
            "response_time_ms": 0.0,
            "root_status_code": None,
            "openapi_discovered": False,
            "openapi_url": None,
            "openapi_version": None,
            "auth_required": False,
            "detected_auth_schemes": [],
            "total_endpoints": 0,
            "object_endpoints": 0,
            "collection_endpoints": 0,
            "checklist": [c.to_dict() for c in checklist],
            "message": "The provided target URL format is invalid.",
            "what_next": "Provide a valid HTTP or HTTPS URL (e.g., http://localhost:8000).",
        }

    # 2. Network Reachability & HTTP Connectivity
    start_time = time.perf_counter()
    root_status_code: int | None = None
    root_content_type = ""
    reachable = False
    auth_required = False

    limits = httpx.Limits(max_connections=5, max_keepalive_connections=2)
    with httpx.Client(timeout=timeout, follow_redirects=True, limits=limits) as client:
        try:
            root_res = client.get(normalized)
            latency_ms = round((time.perf_counter() - start_time) * 1000, 1)
            reachable = True
            root_status_code = root_res.status_code
            root_content_type = root_res.headers.get("content-type", "")

            checklist.append(
                PreflightCheckResult(
                    name="network_reachability",
                    label="NETWORK REACHABILITY",
                    status="pass",
                    detail=f"Host responded in {latency_ms}ms",
                )
            )

            if root_status_code in (401, 403):
                auth_required = True
                checklist.append(
                    PreflightCheckResult(
                        name="http_connectivity",
                        label="HTTP CONNECTIVITY",
                        status="pass",
                        detail=f"HTTP {root_status_code} (Authentication boundary active)",
                    )
                )
            elif root_status_code == 404:
                checklist.append(
                    PreflightCheckResult(
                        name="http_connectivity",
                        label="HTTP CONNECTIVITY",
                        status="warn",
                        detail="Root endpoint returned 404 (Probing for API specifications)",
                    )
                )
            else:
                checklist.append(
                    PreflightCheckResult(
                        name="http_connectivity",
                        label="HTTP CONNECTIVITY",
                        status="pass",
                        detail=f"HTTP {root_status_code} ({root_content_type.split(';')[0] or 'OK'})",
                    )
                )

        except httpx.ConnectTimeout:
            latency_ms = round((time.perf_counter() - start_time) * 1000, 1)
            checklist.append(
                PreflightCheckResult(
                    name="network_reachability",
                    label="NETWORK REACHABILITY",
                    status="fail",
                    detail=f"Connection timed out after {latency_ms}ms",
                )
            )
            return {
                "status": "TIMEOUT",
                "state_code": "TIMEOUT",
                "target_url": normalized,
                "reachable": False,
                "response_time_ms": latency_ms,
                "root_status_code": None,
                "openapi_discovered": False,
                "openapi_url": None,
                "openapi_version": None,
                "auth_required": False,
                "detected_auth_schemes": [],
                "total_endpoints": 0,
                "object_endpoints": 0,
                "collection_endpoints": 0,
                "checklist": [c.to_dict() for c in checklist],
                "message": "Target API did not respond within the connection timeout.",
                "what_next": "Ensure the target API server is online and unblocked by firewall.",
            }
        except (httpx.ConnectError, httpx.NetworkError) as exc:
            checklist.append(
                PreflightCheckResult(
                    name="network_reachability",
                    label="NETWORK REACHABILITY",
                    status="fail",
                    detail=f"Connection refused ({type(exc).__name__})",
                )
            )
            return {
                "status": "NETWORK_ERROR",
                "state_code": "NETWORK_ERROR",
                "target_url": normalized,
                "reachable": False,
                "response_time_ms": 0.0,
                "root_status_code": None,
                "openapi_discovered": False,
                "openapi_url": None,
                "openapi_version": None,
                "auth_required": False,
                "detected_auth_schemes": [],
                "total_endpoints": 0,
                "object_endpoints": 0,
                "collection_endpoints": 0,
                "checklist": [c.to_dict() for c in checklist],
                "message": "Connection to target API was refused or unreachable.",
                "what_next": "Verify the target host and port. For local testing, ensure the sandbox is running on port 8000.",
            }
        except Exception as exc:
            checklist.append(
                PreflightCheckResult(
                    name="network_reachability",
                    label="NETWORK REACHABILITY",
                    status="fail",
                    detail=f"Network error: {str(exc)}",
                )
            )
            return {
                "status": "NETWORK_ERROR",
                "state_code": "NETWORK_ERROR",
                "target_url": normalized,
                "reachable": False,
                "response_time_ms": 0.0,
                "root_status_code": None,
                "openapi_discovered": False,
                "openapi_url": None,
                "openapi_version": None,
                "auth_required": False,
                "detected_auth_schemes": [],
                "total_endpoints": 0,
                "object_endpoints": 0,
                "collection_endpoints": 0,
                "checklist": [c.to_dict() for c in checklist],
                "message": f"Unexpected network failure: {str(exc)}",
                "what_next": "Check the URL and host connectivity.",
            }

        # 3. OpenAPI / Swagger Discovery
        discovered_spec: dict[str, Any] | None = None
        discovered_spec_url: str | None = None

        for path in OPENAPI_CANDIDATE_PATHS:
            spec_candidate = f"{normalized}{path}"
            try:
                spec_res = client.get(spec_candidate)
                if spec_res.status_code == 200:
                    spec_json = spec_res.json()
                    if isinstance(spec_json, dict) and ("openapi" in spec_json or "swagger" in spec_json or "paths" in spec_json):
                        discovered_spec = spec_json
                        discovered_spec_url = spec_candidate
                        break
            except Exception:
                continue

        if not discovered_spec:
            checklist.append(
                PreflightCheckResult(
                    name="openapi_discovery",
                    label="OPENAPI DISCOVERY",
                    status="fail",
                    detail="No valid OpenAPI/Swagger specification found across probe paths",
                )
            )
            return {
                "status": "OPENAPI_NOT_FOUND",
                "state_code": "OPENAPI_NOT_FOUND",
                "target_url": normalized,
                "reachable": reachable,
                "response_time_ms": latency_ms,
                "root_status_code": root_status_code,
                "openapi_discovered": False,
                "openapi_url": None,
                "openapi_version": None,
                "auth_required": auth_required,
                "detected_auth_schemes": [],
                "total_endpoints": 0,
                "object_endpoints": 0,
                "collection_endpoints": 0,
                "checklist": [c.to_dict() for c in checklist],
                "message": "Target API is reachable, but does not expose /openapi.json or /swagger.json.",
                "what_next": "Ensure the target API provides an OpenAPI specification endpoint.",
            }

        checklist.append(
            PreflightCheckResult(
                name="openapi_discovery",
                label="OPENAPI DISCOVERED",
                status="pass",
                detail=f"Discovered specification at {discovered_spec_url}",
            )
        )

        # 4. OpenAPI Parsing & Endpoint Extraction
        try:
            parser = OpenAPIParser(discovered_spec)
            endpoints = parser.endpoints
            object_endpoints = parser.get_object_endpoints()
            collection_endpoints = parser.get_collection_endpoints()
            auth_schemes = list(parser.security_schemes.keys())

            checklist.append(
                PreflightCheckResult(
                    name="openapi_parsed",
                    label="OPENAPI PARSED",
                    status="pass",
                    detail=f"Version {parser.version} · '{parser.title}'",
                )
            )

            checklist.append(
                PreflightCheckResult(
                    name="endpoints_discovered",
                    label=f"{len(endpoints)} ENDPOINTS DISCOVERED",
                    status="pass",
                    detail=f"Mapped {len(endpoints)} HTTP operations across API paths",
                )
            )

            if object_endpoints:
                checklist.append(
                    PreflightCheckResult(
                        name="object_endpoints",
                        label=f"{len(object_endpoints)} OBJECT ENDPOINTS",
                        status="pass",
                        detail=f"{len(object_endpoints)} resource endpoints available for BOLA testing",
                    )
                )
            else:
                checklist.append(
                    PreflightCheckResult(
                        name="object_endpoints",
                        label="0 OBJECT ENDPOINTS",
                        status="warn",
                        detail="No path-parameterized endpoints found for object authorization testing",
                    )
                )

            if auth_schemes or auth_required:
                checklist.append(
                    PreflightCheckResult(
                        name="auth_detection",
                        label="AUTHENTICATION REQUIRED",
                        status="pass",
                        detail=f"Detected schemes: {', '.join(auth_schemes) if auth_schemes else 'Header Token'}",
                    )
                )
            else:
                checklist.append(
                    PreflightCheckResult(
                        name="auth_detection",
                        label="AUTHENTICATION SCHEMES",
                        status="warn",
                        detail="No explicit security schemes defined in OpenAPI (using default profiles)",
                    )
                )

        except Exception as exc:
            checklist.append(
                PreflightCheckResult(
                    name="openapi_parsed",
                    label="OPENAPI PARSED",
                    status="fail",
                    detail=f"Failed to parse OpenAPI document: {str(exc)}",
                )
            )
            return {
                "status": "INVALID_OPENAPI",
                "state_code": "INVALID_OPENAPI",
                "target_url": normalized,
                "reachable": reachable,
                "response_time_ms": latency_ms,
                "root_status_code": root_status_code,
                "openapi_discovered": True,
                "openapi_url": discovered_spec_url,
                "openapi_version": None,
                "auth_required": auth_required,
                "detected_auth_schemes": [],
                "total_endpoints": 0,
                "object_endpoints": 0,
                "collection_endpoints": 0,
                "checklist": [c.to_dict() for c in checklist],
                "message": f"Discovered OpenAPI file at {discovered_spec_url} is malformed or invalid.",
                "what_next": "Check the OpenAPI JSON format for syntax errors.",
            }

        # 5. Scan Readiness Evaluation
        scan_ready = len(endpoints) > 0
        state = "SCAN_READY" if scan_ready else "SCAN_NOT_READY"

        return {
            "status": state,
            "state_code": state,
            "target_url": normalized,
            "reachable": True,
            "response_time_ms": latency_ms,
            "root_status_code": root_status_code,
            "openapi_discovered": True,
            "openapi_url": discovered_spec_url,
            "openapi_version": parser.version,
            "api_title": parser.title,
            "auth_required": bool(auth_schemes or auth_required),
            "detected_auth_schemes": auth_schemes,
            "total_endpoints": len(endpoints),
            "object_endpoints": len(object_endpoints),
            "collection_endpoints": len(collection_endpoints),
            "endpoints": [ep.to_dict() for ep in endpoints],
            "checklist": [c.to_dict() for c in checklist],
            "message": "Target API preflight successful. Specification and attack surface mapped.",
            "what_next": "Define or verify authentication identities, then start the zero-trust security scan.",
        }
