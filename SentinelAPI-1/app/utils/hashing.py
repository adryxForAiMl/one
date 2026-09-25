from hashlib import sha256
from typing import Any


def hash_string(input_string: str) -> str:
    """Hash a string using SHA-256."""
    return sha256(input_string.encode('utf-8')).hexdigest()


def hash_dict(input_dict: dict[str, Any]) -> str:
    """Hash a dictionary by converting it to a sorted JSON string and then hashing it."""
    import json
    normalized = json.dumps(input_dict, sort_keys=True)
    return hash_string(normalized)