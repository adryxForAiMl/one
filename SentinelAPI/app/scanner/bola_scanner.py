import httpx


def scan_bola(
    base_url: str,
    credentials: dict[str, str]
):
    findings = []

    with httpx.Client(timeout=10.0) as client:

        # Step 1: Get the API specification
        spec_response = client.get(
            f"{base_url}/openapi.json"
        )

        spec_response.raise_for_status()
        spec = spec_response.json()

        paths = spec.get("paths", {})

        # Step 2: Find collection endpoints
        collection_endpoints = []

        for path, methods in paths.items():

            if "get" not in methods:
                continue

            if "{" not in path:
                collection_endpoints.append(path)

        # Step 3: Look for related object endpoints
        for collection_path in collection_endpoints:

            object_path = collection_path.rstrip("/") + "/{id}"

            matching_object_path = None

            for path in paths:

                if path.startswith(
                    collection_path.rstrip("/") + "/{"
                ):
                    if "get" in paths[path]:
                        matching_object_path = path
                        break

            if not matching_object_path:
                continue

            # Step 4: Get objects belonging to each user
            discovered_objects = {}

            for user_name, token in credentials.items():

                headers = {
                    "Authorization": token
                }

                response = client.get(
                    f"{base_url}{collection_path}",
                    headers=headers
                )

                if response.status_code != 200:
                    continue

                data = response.json()

                if not isinstance(data, list):
                    continue

                discovered_objects[user_name] = data

            # Step 5: Compare objects between users
            users = list(discovered_objects.keys())

            for current_user in users:

                current_objects = discovered_objects[
                    current_user
                ]

                current_ids = {
                    item.get("order_id")
                    for item in current_objects
                    if item.get("order_id") is not None
                }

                for other_user in users:

                    if current_user == other_user:
                        continue

                    other_objects = discovered_objects[
                        other_user
                    ]

                    for other_object in other_objects:

                        object_id = other_object.get("order_id")

                        if object_id is None:
                            continue

                        if object_id in current_ids:
                            continue

                        test_path = matching_object_path.replace(
                            "{order_id}",
                            str(object_id)
                        )

                        # Try the discovered path
                        response = client.get(
                            f"{base_url}{test_path}",
                            headers={
                                "Authorization":
                                credentials[current_user]
                            }
                        )

                        if response.status_code != 200:
                            continue

                        leaked_data = response.json()

                        owner_id = leaked_data.get(
                            "owner_id"
                        )

                        other_owner_id = other_object.get(
                            "owner_id"
                        )

                        if (
                            owner_id is not None
                            and other_owner_id is not None
                            and owner_id == other_owner_id
                        ):

                            findings.append({
                                "type": "BOLA",
                                "severity": "CRITICAL",
                                "endpoint": test_path,
                                "attacker": current_user,
                                "resource_owner": other_user,
                                "object_id": object_id,
                                "evidence": leaked_data,
                                "description":
                                    "Authenticated user accessed "
                                    "another user's object."
                            })

    return findings