from starlette.testclient import TestClient
from fastapi_starter_project.core.config import settings


def test_me_unauthenticated(client: TestClient) -> None:
    response = client.get("/me")
    assert response.status_code == 401
    assert "detail" in response.json()


def test_login_invalid_credentials(client: TestClient) -> None:
    response = client.post(
        "/login",
        json={"username": "invaliduser", "password": "wrongpassword"},
    )
    assert response.status_code == 401


def test_login_and_access_protected_me(client: TestClient) -> None:
    # 1. Login with valid dummy user credentials
    login_response = client.post(
        "/login",
        json={"username": "johndoe", "password": "password123"},
    )
    assert login_response.status_code == 200
    assert settings.COOKIE_NAME in login_response.cookies

    # 2. Access protected /me using the session cookies
    me_response = client.get("/me", cookies=login_response.cookies)
    assert me_response.status_code == 200
    user_data = me_response.json()
    assert user_data["username"] == "johndoe"
    assert user_data["email"] == "johndoe@example.com"
    assert "password" not in user_data
    assert "hashed_password" not in user_data

    # 3. Access versioned /api/v1/me
    v1_me_response = client.get("/api/v1/me", cookies=login_response.cookies)
    assert v1_me_response.status_code == 200
    assert v1_me_response.json()["username"] == "johndoe"

    # 4. Logout
    logout_response = client.post("/logout")
    assert logout_response.status_code == 200
