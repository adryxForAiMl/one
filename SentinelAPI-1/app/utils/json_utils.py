from typing import Any, Dict, List

def json_response(data: Any, status_code: int = 200) -> Dict[str, Any]:
    return {
        "status": "success",
        "data": data,
        "status_code": status_code,
    }

def json_error(message: str, status_code: int = 400) -> Dict[str, Any]:
    return {
        "status": "error",
        "message": message,
        "status_code": status_code,
    }

def json_list_response(data: List[Any], total: int, status_code: int = 200) -> Dict[str, Any]:
    return {
        "status": "success",
        "data": data,
        "total": total,
        "status_code": status_code,
    }