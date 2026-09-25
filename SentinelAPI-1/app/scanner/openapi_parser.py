from __future__ import annotations

import json
from typing import Any, Dict, List

class OpenAPIParser:
    def __init__(self, spec: dict[str, Any]):
        self.spec = spec

    def get_object_endpoints(self) -> List[Endpoint]:
        endpoints = []
        paths = self.spec.get("paths", {})
        for path, methods in paths.items():
            for method, details in methods.items():
                if "parameters" in details:
                    for param in details["parameters"]:
                        if param.get("in") == "path" and "required" in param and param["required"]:
                            endpoints.append(Endpoint(path, method, param["name"]))
        return endpoints

    def find_paired_collection(self, endpoint: Endpoint) -> Endpoint | None:
        collection_path = endpoint.path.split("/{")[0]
        if collection_path in self.spec.get("paths", {}):
            return Endpoint(collection_path, "GET", endpoint.parameter)
        return None

class Endpoint:
    def __init__(self, path: str, method: str, parameter: str):
        self.path = path
        self.method = method
        self.parameter = parameter

    def __repr__(self):
        return f"Endpoint(path={self.path}, method={self.method}, parameter={self.parameter})"

def parse_openapi_spec(spec: Dict[str, Any]) -> List[Endpoint]:
    parser = OpenAPIParser(spec)
    return parser.get_object_endpoints()