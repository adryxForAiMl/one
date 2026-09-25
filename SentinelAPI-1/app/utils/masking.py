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


def mask_json(data: Any) -> Any:
    """Recursively mask sensitive fields in JSON-like structures."""
    if isinstance(data, dict):
        return {k: mask_json(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [mask_json(item) for item in data]
    return data