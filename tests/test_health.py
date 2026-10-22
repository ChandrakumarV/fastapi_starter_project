from starlette.testclient import TestClient


def test_health_check_unversioned(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "timestamp" in data
    # Server health
    assert data["server"]["status"] == "healthy"
    assert "version" in data["server"]
    assert "environment" in data["server"]
    # Database health
    assert data["database"]["status"] == "connected"
    assert "details" in data["database"]


def test_openapi_has_no_bearer_auth_requirements(client: TestClient) -> None:
    res = client.get("/openapi.json")
    assert res.status_code == 200
    schema = res.json()

    # 1. Global security must be empty/None
    assert "security" not in schema or not schema["security"]

    # 2. components.securitySchemes must not contain Bearer auth
    security_schemes = schema.get("components", {}).get("securitySchemes", {})
    assert not any(
        (isinstance(v, dict) and v.get("scheme") == "bearer") or "bearer" in k.lower()
        for k, v in security_schemes.items()
    )

    # 3. No endpoint operation should declare a security requirement
    for path_item in schema.get("paths", {}).values():
        if isinstance(path_item, dict):
            for operation in path_item.values():
                if isinstance(operation, dict):
                    assert "security" not in operation

