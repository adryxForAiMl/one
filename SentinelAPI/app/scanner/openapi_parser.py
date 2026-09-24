"""
OpenAPI and Swagger Specification Ingestion Layer.
Supports OpenAPI 3.0.x, 3.1.x, and Swagger 2.0.
Extracts normalized endpoint models, security schemes, parameters,
and maps relationships between collection and object endpoints.
"""

from __future__ import annotations

import re
from typing import Any


def resolve_local_ref(spec: dict[str, Any], ref: str) -> dict[str, Any] | None:
    """Resolve a local JSON schema reference (e.g. #/components/schemas/User)."""
    if not ref.startswith("#/"):
        return None
    parts = ref[2:].split("/")
    current: Any = spec
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current if isinstance(current, dict) else None


class NormalizedEndpoint:
    def __init__(
        self,
        path: str,
        method: str,
        operation_id: str | None = None,
        summary: str | None = None,
        description: str | None = None,
        tags: list[str] | None = None,
        parameters: list[dict[str, Any]] | None = None,
        path_parameters: list[str] | None = None,
        query_parameters: list[str] | None = None,
        header_parameters: list[str] | None = None,
        request_body_schema: dict[str, Any] | None = None,
        response_schemas: dict[str, Any] | None = None,
        security_schemes: list[str] | None = None,
        category: str = "collection",
        collection_path: str | None = None,
        parameter: str | None = None,
        resource_name: str | None = None,
    ):
        self.path = path
        self.method = method.upper()
        self.operation_id = operation_id
        self.summary = summary
        self.description = description
        self.tags = tags or []
        self.parameters = parameters or []
        self.path_parameters = path_parameters or []
        self.query_parameters = query_parameters or []
        self.header_parameters = header_parameters or []
        self.request_body_schema = request_body_schema
        self.response_schemas = response_schemas or {}
        self.security_schemes = security_schemes or []
        self.category = category  # 'object' | 'collection' | 'utility'
        self.collection_path = collection_path
        self.parameter = parameter
        self.resource_name = resource_name

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "method": self.method,
            "operation_id": self.operation_id,
            "summary": self.summary,
            "description": self.description,
            "tags": self.tags,
            "parameters": self.parameters,
            "path_parameters": self.path_parameters,
            "query_parameters": self.query_parameters,
            "header_parameters": self.header_parameters,
            "category": self.category,
            "collection_path": self.collection_path,
            "parameter": self.parameter,
            "resource_name": self.resource_name,
            "security_schemes": self.security_schemes,
            "authorization_tested": (
                self.method == "GET" and self.category == "object"
            ),
        }


class OpenAPIParser:
    """Parser for OpenAPI 3.x and Swagger 2.0 specifications."""

    def __init__(self, spec: dict[str, Any]):
        if not isinstance(spec, dict):
            raise ValueError("OpenAPI specification must be a dictionary.")
        self.spec = spec
        self.version = self._detect_version()
        self.title = self._extract_title()
        self.security_schemes = self._extract_security_schemes()
        self.endpoints = self._extract_endpoints()

    def _detect_version(self) -> str:
        if "openapi" in self.spec:
            return str(self.spec["openapi"])
        if "swagger" in self.spec:
            return str(self.spec["swagger"])
        return "3.0.0"

    def _extract_title(self) -> str:
        info = self.spec.get("info", {})
        if isinstance(info, dict):
            return str(info.get("title", "Target API"))
        return "Target API"

    def _extract_security_schemes(self) -> dict[str, dict[str, Any]]:
        schemes: dict[str, dict[str, Any]] = {}
        # OpenAPI 3.x
        components = self.spec.get("components", {})
        if isinstance(components, dict):
            comp_schemes = components.get("securitySchemes", {})
            if isinstance(comp_schemes, dict):
                for name, details in comp_schemes.items():
                    if isinstance(details, dict):
                        schemes[name] = details

        # Swagger 2.0
        sec_definitions = self.spec.get("securityDefinitions", {})
        if isinstance(sec_definitions, dict):
            for name, details in sec_definitions.items():
                if isinstance(details, dict) and name not in schemes:
                    schemes[name] = details

        return schemes

    def _extract_endpoints(self) -> list[NormalizedEndpoint]:
        paths = self.spec.get("paths", {})
        if not isinstance(paths, dict):
            return []

        allowed_methods = {
            "get",
            "post",
            "put",
            "patch",
            "delete",
            "head",
            "options",
        }
        all_paths = list(paths.keys())
        endpoints: list[NormalizedEndpoint] = []

        for path, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue

            # Shared path-level parameters
            path_level_params = path_item.get("parameters", [])
            if not isinstance(path_level_params, list):
                path_level_params = []

            for method_name, method_details in path_item.items():
                if str(method_name).lower() not in allowed_methods:
                    continue
                if not isinstance(method_details, dict):
                    continue

                method_upper = str(method_name).upper()
                op_params = method_details.get("parameters", [])
                if not isinstance(op_params, list):
                    op_params = []

                combined_params = path_level_params + op_params

                # Extract path parameter names
                raw_path_params = re.findall(r"\{([^}]+)\}", path)
                query_params: list[str] = []
                header_params: list[str] = []
                parsed_params: list[dict[str, Any]] = []

                for param in combined_params:
                    if not isinstance(param, dict):
                        continue
                    p_in = param.get("in", "")
                    p_name = param.get("name", "")
                    if not p_name:
                        continue
                    parsed_params.append({
                        "name": p_name,
                        "in": p_in,
                        "required": param.get("required", False),
                        "type": param.get("schema", {}).get("type") if isinstance(param.get("schema"), dict) else param.get("type", "string"),
                        "description": param.get("description", ""),
                    })
                    if p_in == "query":
                        query_params.append(p_name)
                    elif p_in == "header":
                        header_params.append(p_name)

                # Classify endpoint category
                is_object = len(raw_path_params) > 0
                category = "object" if is_object else "collection"

                primary_param: str | None = None
                collection_path: str | None = None
                resource_name: str | None = None

                if is_object:
                    primary_param = raw_path_params[0]
                    # Inferred collection path e.g. /orders/{order_id} -> /orders
                    parts_before_param = path.split("{" + primary_param + "}")[0].rstrip("/")
                    if parts_before_param:
                        collection_path = parts_before_param
                        # Resource name e.g. /api/v1/orders -> order
                        resource_candidate = parts_before_param.split("/")[-1]
                        if resource_candidate.endswith("s") and len(resource_candidate) > 2:
                            resource_name = resource_candidate[:-1]
                        else:
                            resource_name = resource_candidate
                    else:
                        collection_path = None
                        resource_name = primary_param.replace("_id", "").replace("id", "")
                else:
                    path_segments = [p for p in path.split("/") if p]
                    if path_segments:
                        resource_name = path_segments[-1]

                # Security schemes
                sec_list: list[str] = []
                op_sec = method_details.get("security", self.spec.get("security", []))
                if isinstance(op_sec, list):
                    for sec_item in op_sec:
                        if isinstance(sec_item, dict):
                            sec_list.extend(sec_item.keys())

                endpoint = NormalizedEndpoint(
                    path=path,
                    method=method_upper,
                    operation_id=method_details.get("operationId"),
                    summary=method_details.get("summary"),
                    description=method_details.get("description"),
                    tags=method_details.get("tags", []),
                    parameters=parsed_params,
                    path_parameters=raw_path_params,
                    query_parameters=query_params,
                    header_parameters=header_params,
                    category=category,
                    collection_path=collection_path,
                    parameter=primary_param,
                    resource_name=resource_name,
                    security_schemes=sec_list,
                )
                endpoints.append(endpoint)

        endpoints.sort(key=lambda ep: (ep.path, ep.method))
        return endpoints

    def get_object_endpoints(self) -> list[NormalizedEndpoint]:
        """Return endpoints that operate on specific objects/resources."""
        return [ep for ep in self.endpoints if ep.category == "object"]

    def get_collection_endpoints(self) -> list[NormalizedEndpoint]:
        """Return collection endpoints that return lists of objects."""
        return [ep for ep in self.endpoints if ep.category == "collection"]

    def find_paired_collection(self, object_endpoint: NormalizedEndpoint) -> NormalizedEndpoint | None:
        """Find the matching GET collection endpoint for an object endpoint."""
        if not object_endpoint.collection_path:
            return None
        for ep in self.endpoints:
            if ep.method == "GET" and ep.path.rstrip("/") == object_endpoint.collection_path.rstrip("/"):
                return ep
        return None
