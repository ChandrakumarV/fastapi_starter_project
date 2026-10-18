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
