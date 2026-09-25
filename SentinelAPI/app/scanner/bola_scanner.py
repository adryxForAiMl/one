"""
KAVACH Raksha - Zero-Trust Authorization Testing Engine.
Implements deterministic Broken Object Level Authorization (BOLA / IDOR) detection,
bidirectional verification, response fingerprinting, excessive data exposure analysis,
and reproducible evidence generation.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

import httpx

from app.scanner.openapi_parser import OpenAPIParser
from app.scanner.target_preflight import OPENAPI_CANDIDATE_PATHS


DEFAULT_TIMEOUT = 10.0

SENSITIVE_KEY_PATTERNS = {
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
    "access_token",
    "private_key",
    "ssn",
    "credit_card",
    "card_number",
    "cvv",
    "pin",
    "tax_id",
    "phone",
    "email",
    "salary",
}


def mask_credential(credential: str | None) -> str:
    """Mask credential string so secrets are never displayed or stored in plaintext."""
    if not credential:
        return "[NONE]"
    cred = str(credential).strip()
    if len(cred) <= 6:
        return "***"
    return f"{cred[:3]}***{cred[-2:]}"


def mask_headers(headers: dict[str, str]) -> dict[str, str]:
    """Return headers with authorization / secret values safely masked."""
    masked: dict[str, str] = {}
    sensitive_headers = {
        "authorization",
        "x-api-key",
        "api-key",
        "token",
        "x-auth-token",
        "cookie",
    }
    for k, v in headers.items():
        if k.lower() in sensitive_headers:
            masked[k] = mask_credential(v)
        else:
            masked[k] = v
    return masked


def find_object_endpoints(spec: dict[str, Any]) -> list[dict[str, Any]]:
    """Legacy compatibility helper + enhanced by OpenAPIParser."""
    try:
        parser = OpenAPIParser(spec)
        object_eps = parser.get_object_endpoints()
        results = []
        for ep in object_eps:
            paired = parser.find_paired_collection(ep)
            results.append({
                "object_path": ep.path,
                "collection_path": paired.path if paired else (ep.collection_path or ep.path.split("/{")[0]),
                "parameter": ep.parameter or "id",
            })
        return results
    except Exception:
        # Fallback to direct inspection
        endpoints = []
        paths = spec.get("paths", {})
        if not isinstance(paths, dict):
            return endpoints

        for path, methods in paths.items():
            if not isinstance(methods, dict) or "get" not in methods:
                continue
            path_params = [
                part[1:-1]
                for part in path.split("/")
                if part.startswith("{") and part.endswith("}")
            ]
            if len(path_params) == 1:
                param = path_params[0]
                collection_path = path.split("/{" + param + "}")[0]
                if collection_path and collection_path in paths:
                    endpoints.append({
                        "object_path": path,
                        "collection_path": collection_path,
                        "parameter": param,
                    })
        return endpoints


def get_object_id(item: Any, parameter: str) -> Any:
    """Extract object identifier from a data dictionary."""
    if not isinstance(item, dict):
        return None

    candidates = [
        parameter,
        "id",
        f"{parameter}_id",
    ]
    if parameter.endswith("_id"):
        candidates.append(parameter[:-3] + "_id")
        candidates.append(parameter[:-3])

    for key in candidates:
        if key in item and item[key] is not None:
            return item[key]

    return None


def build_headers(
    credential: str | None,
    auth_type: str = "authorization",
    auth_header: str = "Authorization",
) -> dict[str, str]:
    """Construct HTTP headers based on authentication profile type."""
    if not credential:
        return {}

    if auth_type == "bearer":
        return {"Authorization": f"Bearer {credential}"}

    if auth_type == "api-key":
        return {auth_header: credential}

    return {auth_header: credential}


def safe_json(response: httpx.Response) -> Any:
    """Safely parse JSON response or return None."""
    try:
        return response.json()
    except (ValueError, TypeError):
        return None


def response_fingerprint(response: httpx.Response, parsed_body: Any) -> str:
    """Generate SHA256 response fingerprint based on status, type, and normalized body."""
    if parsed_body is not None:
        try:
            normalized = json.dumps(parsed_body, sort_keys=True, default=str)
        except (TypeError, ValueError):
            normalized = str(parsed_body)
    else:
        normalized = response.text

    raw = f"{response.status_code}|{response.headers.get('content-type', '')}|{normalized}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def extract_response_metadata(response: httpx.Response, body: Any) -> dict[str, Any]:
    """Extract structured metadata from HTTP response for security analysis."""
    return {
        "status_code": response.status_code,
        "content_type": response.headers.get("content-type", "application/json"),
        "content_length": len(response.content),
        "body_type": type(body).__name__,
        "body_hash": response_fingerprint(response, body),
        "headers": {
            k: v
            for k, v in response.headers.items()
            if k.lower() in ("content-type", "server", "x-request-id", "cache-control")
        },
    }


def detect_sensitive_fields(data: Any) -> list[str]:
    """Inspect returned payload keys for excessive data exposure."""
    exposed: list[str] = []
    if isinstance(data, dict):
        for k, v in data.items():
            key_lower = str(k).lower()
            if any(p in key_lower for p in SENSITIVE_KEY_PATTERNS):
                exposed.append(str(k))
            if isinstance(v, (dict, list)):
                exposed.extend(detect_sensitive_fields(v))
    elif isinstance(data, list):
        for item in data:
            exposed.extend(detect_sensitive_fields(item))
    return sorted(set(exposed))


def build_developer_remediation(
    endpoint: str,
    method: str,
    parameter: str,
    resource_name: str = "resource",
) -> dict[str, Any]:
    """Generate comprehensive developer remediation instructions and code verification."""
    return {
        "what_happened": (
            f"The endpoint {method} {endpoint} returned protected data to an authenticated "
            "identity who is neither the owner nor authorized to access this specific object."
        ),
        "why_it_matters": (
            "Broken Object Level Authorization (OWASP API1) allows authenticated attackers "
            "to enumerate IDs and exfiltrate private records belonging to other users or organizations, "
            "leading to widespread data breaches and compliance violations."
        ),
        "how_to_fix": (
            "Enforce server-side object ownership verification. Always check that the current "
            "authenticated user identity owns or has explicit permission for the requested object "
            "before retrieving and returning the resource."
        ),
        "code_example": {
            "vulnerable": f"""# Vulnerable implementation
@app.get("{endpoint}")
def get_{resource_name}({parameter}: int, user = Depends(get_current_user)):
    {resource_name} = db.find({parameter})
    if not {resource_name}:
        raise HTTPException(status_code=404)
    return {resource_name}  # Missing ownership check!""",
            "remediated": f"""# Remediated zero-trust implementation
@app.get("{endpoint}")
def get_{resource_name}({parameter}: int, user = Depends(get_current_user)):
    {resource_name} = db.find({parameter})
    if not {resource_name}:
        raise HTTPException(status_code=404)
    # Zero-Trust Check: verify ownership
    if {resource_name}.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return {resource_name}""",
        },
        "fix_verification": (
            "After remediation, repeat the cross-user request. The server must deny access with "
            "HTTP 403 Forbidden (or HTTP 404 Not Found to prevent ID enumeration)."
        ),
    }


def scan_bola(
    base_url: str,
    credentials: dict[str, str],
    auth_type: str = "authorization",
    auth_header: str = "Authorization",
) -> list[dict[str, Any]]:
    """
    Execute deterministic zero-trust BOLA authorization testing.
    Validates cross-user object access with bidirectional testing and evidence capture.
    """
    findings: list[dict[str, Any]] = []

    if len(credentials) < 2:
        return findings

    base_url = base_url.rstrip("/")
    limits = httpx.Limits(max_connections=10, max_keepalive_connections=5)

    with httpx.Client(timeout=DEFAULT_TIMEOUT, follow_redirects=True, limits=limits) as client:
        # Fetch OpenAPI specification
        spec: dict[str, Any] | None = None
        for path in OPENAPI_CANDIDATE_PATHS:
            try:
                res = client.get(f"{base_url}{path}")
                if res.status_code == 200:
                    spec = res.json()
                    break
            except Exception:
                continue

        if not spec:
            return findings

        endpoints = find_object_endpoints(spec)

        for endpoint_info in endpoints:
            object_path = endpoint_info["object_path"]
            collection_path = endpoint_info["collection_path"]
            parameter = endpoint_info["parameter"]

            user_objects: dict[str, list[dict[str, Any]]] = {}
            user_collection_responses: dict[str, dict[str, Any]] = {}

            # Step 1: Collect legitimate objects for each identity
            for user_name, credential in credentials.items():
                headers = build_headers(credential, auth_type, auth_header)
                try:
                    res = client.get(f"{base_url}{collection_path}", headers=headers)
                except httpx.RequestError:
                    continue

                body = safe_json(res)
                user_collection_responses[user_name] = {
                    "status_code": res.status_code,
                    "metadata": extract_response_metadata(res, body),
                }

                if res.status_code != 200 or not isinstance(body, list):
                    continue

                objects = []
                for item in body:
                    obj_id = get_object_id(item, parameter)
                    if obj_id is not None:
                        objects.append(item)
                user_objects[user_name] = objects

            users = list(user_objects.keys())
            cross_tests: list[tuple[str, str, dict[str, Any]]] = []

            # Step 2: Build cross-user access test pairs
            for attacker in users:
                attacker_objects = user_objects.get(attacker, [])
                attacker_ids = {
                    get_object_id(item, parameter)
                    for item in attacker_objects
                }

                for victim in users:
                    if attacker == victim:
                        continue

                    victim_objects = user_objects.get(victim, [])
                    for victim_obj in victim_objects:
                        victim_id = get_object_id(victim_obj, parameter)
                        if victim_id is None or victim_id in attacker_ids:
                            continue
                        cross_tests.append((attacker, victim, victim_obj))

            # Step 3: Execute cross-identity authorization tests
            for attacker, victim, victim_obj in cross_tests:
                victim_id = get_object_id(victim_obj, parameter)
                target_path = object_path.replace(f"{{{parameter}}}", str(victim_id))
                attacker_headers = build_headers(credentials[attacker], auth_type, auth_header)

                try:
                    response = client.get(f"{base_url}{target_path}", headers=attacker_headers)
                except httpx.RequestError:
                    continue

                leaked_data = safe_json(response)
                if response.status_code != 200:
                    continue

                leaked_id = get_object_id(leaked_data, parameter)
                if leaked_id != victim_id:
                    continue

                # Cross-user access confirmed!
                response_metadata = extract_response_metadata(response, leaked_data)
                sensitive_fields = detect_sensitive_fields(leaked_data)
                finding_number = len(findings) + 1
                finding_id = f"BOLA-{finding_number:03d}"
                timestamp = datetime.now(timezone.utc).isoformat()

                remediation_details = build_developer_remediation(
                    endpoint=object_path,
                    method="GET",
                    parameter=parameter,
                    resource_name="order",
                )

                findings.append({
                    "id": finding_id,
                    "title": "Broken Object Level Authorization (BOLA / IDOR)",
                    "type": "BOLA",
                    "severity": "CRITICAL",
                    "confidence": 1.0,
                    "confidence_label": "VERY HIGH",
                    "category": "Broken Object Level Authorization",
                    "cwe": "CWE-639",
                    "cwe_title": "Authorization Bypass Through User-Controlled Key",
                    "owasp": "API1:2023 - Broken Object Level Authorization",
                    "endpoint": target_path,
                    "endpoint_template": object_path,
                    "method": "GET",
                    "attacker": attacker,
                    "resource_owner": victim,
                    "object_id": victim_id,
                    "status_code": response.status_code,
                    "status": "vulnerable",
                    "timestamp": timestamp,
                    "verification": {
                        "cross_identity": True,
                        "ownership_mismatch": True,
                        "successful_access": True,
                        "object_identity_matched": True,
                        "bidirectional_tested": True,
                    },
                    "evidence": {
                        "finding_id": finding_id,
                        "timestamp": timestamp,
                        "request": {
                            "method": "GET",
                            "url": target_path,
                            "user": attacker,
                            "headers": mask_headers(attacker_headers),
                        },
                        "response": leaked_data,
                        "response_metadata": response_metadata,
                        "response_fingerprint": response_metadata["body_hash"],
                        "attacker_collection": user_collection_responses.get(attacker),
                        "resource_owner_collection": user_collection_responses.get(victim),
                        "sensitive_fields_exposed": sensitive_fields,
                    },
                    "impact": (
                        f"An authenticated user ('{attacker}') successfully read protected records "
                        f"belonging to another user ('{victim}') without possessing ownership or permission."
                    ),
                    "remediation": remediation_details["how_to_fix"],
                    "developer_remediation": remediation_details,
                    "description": (
                        "Broken Object Level Authorization detected. The API returned an object "
                        "belonging to another authenticated user with HTTP 200 OK."
                    ),
                    "security_reasoning": [
                        f"Attacker authenticated as '{attacker}' with valid credentials.",
                        f"Object #{victim_id} was absent from {attacker}'s authorized collection.",
                        f"Object #{victim_id} was confirmed owned by '{victim}'.",
                        f"Attacker requested target path '{target_path}'.",
                        f"Server returned HTTP {response.status_code} with matching object ID #{victim_id}.",
                        "Deterministic cross-identity authorization failure verified.",
                    ],
                })

    return findings