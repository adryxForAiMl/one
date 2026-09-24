import httpx


def find_object_endpoints(spec):
    endpoints = []

    for path, methods in spec.get("paths", {}).items():

        if "get" not in methods:
            continue

        path_parameters = [
            part[1:-1]
            for part in path.split("/")
            if part.startswith("{") and part.endswith("}")
        ]

        if len(path_parameters) != 1:
            continue

        parameter = path_parameters[0]
        collection_path = path.split("/{")[0]

        if collection_path == path:
            continue

        if collection_path not in spec.get("paths", {}):
            continue

        if "get" not in spec["paths"][collection_path]:
            continue

        endpoints.append({
            "object_path": path,
            "collection_path": collection_path,
            "parameter": parameter
        })

    return endpoints


def get_object_id(item, parameter):
    if not isinstance(item, dict):
        return None

    candidates = [
        parameter,
        "id"
    ]

    if parameter.endswith("_id"):
        candidates.append(parameter[:-3] + "_id")

    for key in candidates:
        if key in item:
            return item[key]

    return None


def scan_bola(base_url: str, credentials: dict[str, str]):
    findings = []

    with httpx.Client(timeout=10.0) as client:

        spec_response = client.get(
            f"{base_url}/openapi.json"
        )

        spec_response.raise_for_status()
        spec = spec_response.json()

        endpoints = find_object_endpoints(spec)

        for endpoint in endpoints:

            object_path = endpoint["object_path"]
            collection_path = endpoint["collection_path"]
            parameter = endpoint["parameter"]

            user_objects = {}

            for user_name, token in credentials.items():

                response = client.get(
                    f"{base_url}{collection_path}",
                    headers={
                        "Authorization": token
                    }
                )

                if response.status_code != 200:
                    continue

                data = response.json()

                if not isinstance(data, list):
                    continue

                objects = []

                for item in data:

                    object_id = get_object_id(
                        item,
                        parameter
                    )

                    if object_id is not None:
                        objects.append(item)

                user_objects[user_name] = objects

            users = list(user_objects.keys())

            for attacker in users:

                attacker_objects = user_objects[attacker]

                attacker_ids = {
                    get_object_id(item, parameter)
                    for item in attacker_objects
                }

                for victim in users:

                    if attacker == victim:
                        continue

                    victim_objects = user_objects[victim]

                    for victim_object in victim_objects:

                        victim_id = get_object_id(
                            victim_object,
                            parameter
                        )

                        if victim_id is None:
                            continue

                        if victim_id in attacker_ids:
                            continue

                        target_path = object_path.replace(
                            "{" + parameter + "}",
                            str(victim_id)
                        )

                        response = client.get(
                            f"{base_url}{target_path}",
                            headers={
                                "Authorization": credentials[attacker]
                            }
                        )

                        if response.status_code != 200:
                            continue

                        leaked_data = response.json()

                        leaked_id = get_object_id(
                            leaked_data,
                            parameter
                        )

                        if leaked_id == victim_id:

                            findings.append({
                                "id": f"BOLA-{len(findings) + 1:03d}",

                                "type": "BOLA",
                                "severity": "CRITICAL",

                                "endpoint": target_path,
                                "method": "GET",

                                "attacker": attacker,
                                "resource_owner": victim,

                                "object_id": victim_id,

                                "expected": (
                                    "Authenticated user should only access "
                                    "objects they own."
                                ),

                                "actual": (
                                    "Authenticated user successfully accessed "
                                    "another user's object."
                                ),

                                "status_code": response.status_code,

                                "evidence": {
                                    "request": {
                                        "method": "GET",
                                        "url": target_path,
                                        "user": attacker
                                    },
                                    "response": leaked_data
                                },

                                "impact": (
                                    "An authenticated user can access "
                                    "another user's protected resource."
                                ),

                                "remediation": (
                                    "Verify that the authenticated user's identity "
                                    "matches the resource owner before returning "
                                    "the requested object."
                                ),

                                "description": (
                                    "Broken Object Level Authorization detected. "
                                    "The API returned an object belonging to another "
                                    "authenticated user."
                                )
                            })

    return findings