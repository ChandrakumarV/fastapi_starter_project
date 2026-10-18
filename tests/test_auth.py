import uuid
from starlette.testclient import TestClient
from fastapi_starter_project.core.config import settings


def test_me_unauthenticated(client: TestClient) -> None:
    response = client.get("/api/v1/me")
    assert response.status_code == 401
    assert "detail" in response.json()


def test_check_username_availability(client: TestClient) -> None:
    # 1. Existing user 'admin' should be unavailable
    res_taken = client.get("/api/v1/auth/check-username", params={"username": "admin"})
    assert res_taken.status_code == 200
    data_taken = res_taken.json()
    assert data_taken["username"] == "admin"
    assert data_taken["available"] is False
    assert "already taken" in data_taken["message"]

    # 2. Random unassigned username should be available
    random_user = f"available_{uuid.uuid4().hex[:6]}"
    res_avail = client.get("/api/v1/auth/check-username", params={"username": random_user})
    assert res_avail.status_code == 200
    data_avail = res_avail.json()
    assert data_avail["username"] == random_user
    assert data_avail["available"] is True
    assert "is available" in data_avail["message"]


def test_register_and_authenticate_user(client: TestClient) -> None:
    unique_suffix = uuid.uuid4().hex[:6]
    username = f"user_{unique_suffix}"
    email = f"{username}@example.com"
    password = "securepassword123"

    # 1. Register a new user
    register_payload = {
        "username": username,
        "email": email,
        "full_name": "Test User",
        "password": password,
    }
    reg_response = client.post("/api/v1/auth/register", json=register_payload)
    assert reg_response.status_code == 201
    user_data = reg_response.json()
    assert user_data["username"] == username
    assert user_data["role"] == "user"  # Self-registration always grants 'user' role
    assert "password" not in user_data

    # 2. Cannot register with duplicate username
    dup_response = client.post("/api/v1/auth/register", json=register_payload)
    assert dup_response.status_code == 409
    assert "already taken" in dup_response.json()["detail"]

    # 3. Login as new user
    login_response = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert login_response.status_code == 200
    assert settings.COOKIE_NAME in login_response.cookies
    cookie = {settings.COOKIE_NAME: login_response.cookies[settings.COOKIE_NAME]}

    # 4. GET /me
    me_response = client.get("/api/v1/me", cookies=cookie)
    assert me_response.status_code == 200
    assert me_response.json()["username"] == username

    # 5. PUT /me (update profile)
    update_response = client.put(
        "/api/v1/me",
        json={"full_name": "Updated Name"},
        cookies=cookie,
    )
    assert update_response.status_code == 200
    assert update_response.json()["full_name"] == "Updated Name"

    # 6. DELETE /auth/logout
    logout_response = client.delete("/api/v1/auth/logout")
    assert logout_response.status_code == 200

    # 7. DELETE /me (soft delete user account)
    delete_response = client.delete("/api/v1/me", cookies=cookie)
    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == "User account deleted successfully."

    # 8. Attempting to log in as soft-deleted user returns 404 "User not found."
    soft_deleted_login = client.post(
        "/api/v1/auth/login",
        json={"username": username, "password": password},
    )
    assert soft_deleted_login.status_code == 404
    assert soft_deleted_login.json()["detail"] == "User not found."


def test_login_invalid_credentials(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "invaliduser", "password": "wrongpassword"},
    )
    assert response.status_code == 401


def test_admin_cannot_access_user_endpoints(client: TestClient) -> None:
    # 0. Attempting to log in as admin at user /api/v1/auth/login -> 403 Forbidden
    user_login_attempt = client.post(
        "/api/v1/auth/login",
        json={"username": "admin", "password": "password123"},
    )
    assert user_login_attempt.status_code == 403
    assert user_login_attempt.json()["detail"] == "User privileges required to access this endpoint."

    # 1. Login with seeded admin 'admin' via admin endpoint
    admin_login = client.post(
        "/api/v1/admin/auth/login",
        json={"username": "admin", "password": "password123"},
    )
    assert admin_login.status_code == 200
    admin_cookie = {settings.COOKIE_NAME: admin_login.cookies[settings.COOKIE_NAME]}

    # 2. Attempt to access normal user GET /api/v1/me -> 403 Forbidden
    res_get = client.get("/api/v1/me", cookies=admin_cookie)
    assert res_get.status_code == 403
    assert res_get.json()["detail"] == "User access required."

    # 3. Attempt to access normal user PUT /api/v1/me -> 403 Forbidden
    res_put = client.put(
        "/api/v1/me",
        json={"full_name": "Admin Impersonator"},
        cookies=admin_cookie,
    )
    assert res_put.status_code == 403
    assert res_put.json()["detail"] == "User access required."

    # 4. Attempt to access normal user DELETE /api/v1/me -> 403 Forbidden
    res_del = client.delete("/api/v1/me", cookies=admin_cookie)
    assert res_del.status_code == 403
    assert res_del.json()["detail"] == "User access required."
