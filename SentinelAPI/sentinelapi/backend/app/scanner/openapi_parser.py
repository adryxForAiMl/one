from typing import Any, List, Dict

class OpenAPIParser:
    def __init__(self, spec: Dict[str, Any]):
        self.spec = spec

    def get_object_endpoints(self) -> List[Dict[str, Any]]:
        endpoints = []
        paths = self.spec.get("paths", {})
        for path, methods in paths.items():
            for method, details in methods.items():
                if "parameters" in details:
                    for param in details["parameters"]:
                        if param.get("in") == "path":
                            endpoints.append({
                                "path": path,
                                "method": method.upper(),
                                "parameter": param.get("name"),
                                "description": details.get("description", ""),
                            })
        return endpoints

    def find_paired_collection(self, endpoint: Dict[str, Any]) -> Any:
        # This method should find the paired collection endpoint for a given object endpoint
        # For simplicity, we will assume that the collection path is the same as the object path
        # but without the parameter.
        path = endpoint["path"]
        parameter = endpoint["parameter"]
        collection_path = path.replace(f"/{{{parameter}}}", "")
        return {"path": collection_path} if collection_path in self.spec["paths"] else None

    def get_endpoints(self) -> List[Dict[str, Any]]:
        return self.get_object_endpoints()