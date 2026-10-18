import uuid
from starlette.testclient import TestClient
from fastapi_starter_project.core.config import settings


def test_admin_login_rejects_normal_user(client: TestClient) -> None:
    # user is a normal user (role='user')
    response = client.post(
        "/api/v1/admin/auth/login",
        json={"username": "user", "password": "password456"},
    )
    # Must be rejected because role is not admin
    assert response.status_code == 403
    assert "Admin privileges required" in response.json()["detail"]


def test_admin_flow_and_me_crud(client: TestClient) -> None:
    # 1. Login with seeded admin 'admin'
    login_response = client.post(
        "/api/v1/admin/auth/login",
        json={"username": "admin", "password": "password123"},
    )
    assert login_response.status_code == 200
    assert settings.COOKIE_NAME in login_response.cookies
    admin_cookie = {settings.COOKIE_NAME: login_response.cookies[settings.COOKIE_NAME]}

    # 2. GET /admin/me (allowed for admin)
    me_res = client.get("/api/v1/admin/me", cookies=admin_cookie)
    assert me_res.status_code == 200
    assert me_res.json()["username"] == "admin"
    assert me_res.json()["role"] == "admin"

    # 3. PUT /admin/me (update profile)
    put_res = client.put(
        "/api/v1/admin/me",
        json={"full_name": "John Doe Senior"},
        cookies=admin_cookie,
    )
    assert put_res.status_code == 200
    assert put_res.json()["full_name"] == "John Doe Senior"

    # 4. Admin creates another admin user
    new_admin_username = f"admin_{uuid.uuid4().hex[:6]}"
    create_res = client.post(
        "/api/v1/admin/users",
        json={
            "username": new_admin_username,
            "email": f"{new_admin_username}@example.com",
            "full_name": "New Admin",
            "password": "secondadminpassword",
            "role": "admin",
        },
        cookies=admin_cookie,
    )
    assert create_res.status_code == 201
    assert create_res.json()["username"] == new_admin_username
    assert create_res.json()["role"] == "admin"

    # 5. Admin lists all users
    list_res = client.get("/api/v1/admin/users", cookies=admin_cookie)
    assert list_res.status_code == 200
    usernames = [u["username"] for u in list_res.json()]
    assert "admin" in usernames
    assert new_admin_username in usernames

    # 6. DELETE /admin/auth/logout
    logout_res = client.delete("/api/v1/admin/auth/logout")
    assert logout_res.status_code == 200


def test_admin_me_denied_for_normal_user(client: TestClient) -> None:
    # Login as normal user
    login_res = client.post(
        "/api/v1/auth/login",
        json={"username": "user", "password": "password456"},
    )
    assert login_res.status_code == 200
    user_cookie = {settings.COOKIE_NAME: login_res.cookies[settings.COOKIE_NAME]}

    # Attempt to access GET /admin/me
    admin_get = client.get("/api/v1/admin/me", cookies=user_cookie)
    assert admin_get.status_code == 403
    assert admin_get.json()["detail"] == "Admin access required."

    # Attempt to access PUT /admin/me
    admin_put = client.put(
        "/api/v1/admin/me",
        json={"full_name": "User Impersonating Admin"},
        cookies=user_cookie,
    )
    assert admin_put.status_code == 403
    assert admin_put.json()["detail"] == "Admin access required."

    # Attempt to access DELETE /admin/me
    admin_del = client.delete("/api/v1/admin/me", cookies=user_cookie)
    assert admin_del.status_code == 403
    assert admin_del.json()["detail"] == "Admin access required."

    # Attempt to access GET /admin/users
    admin_users = client.get("/api/v1/admin/users", cookies=user_cookie)
    assert admin_users.status_code == 403
    assert admin_users.json()["detail"] == "Admin access required."


def test_admin_toggle_user_active_and_soft_delete(client: TestClient) -> None:
    # 1. Admin login
    admin_login = client.post(
        "/api/v1/admin/auth/login",
        json={"username": "admin", "password": "password123"},
    )
    assert admin_login.status_code == 200
    admin_cookie = {settings.COOKIE_NAME: admin_login.cookies[settings.COOKIE_NAME]}

    # 2. Register a new user
    uid = uuid.uuid4().hex[:6]
    test_user_name = f"user_{uid}"
    test_password = "password123"
    reg_res = client.post(
        "/api/v1/auth/register",
        json={
            "username": test_user_name,
            "email": f"{test_user_name}@example.com",
            "full_name": "Test Subject",
            "password": test_password,
        },
    )
    assert reg_res.status_code == 201
    user_id = reg_res.json()["id"]

    # 3. Admin deactivates user
    deactivate_res = client.patch(
        f"/api/v1/admin/users/{user_id}/status",
        json={"is_active": False},
        cookies=admin_cookie,
    )
    assert deactivate_res.status_code == 200
    assert deactivate_res.json()["is_active"] is False

    # 4. User attempts to login -> 403 Inactive account
    inactive_login = client.post(
        "/api/v1/auth/login",
        json={"username": test_user_name, "password": test_password},
    )
    assert inactive_login.status_code == 403
    assert "Inactive user account" in inactive_login.json()["detail"]

    # 5. Admin reactivates user
    reactivate_res = client.patch(
        f"/api/v1/admin/users/{user_id}/status",
        json={"is_active": True},
        cookies=admin_cookie,
    )
    assert reactivate_res.status_code == 200
    assert reactivate_res.json()["is_active"] is True

    # 6. User logs in successfully
    active_login = client.post(
        "/api/v1/auth/login",
        json={"username": test_user_name, "password": test_password},
    )
    assert active_login.status_code == 200

    # 7. Admin soft-deletes user
    del_res = client.delete(
        f"/api/v1/admin/users/{user_id}",
        cookies=admin_cookie,
    )
    assert del_res.status_code == 200
    assert "deleted successfully" in del_res.json()["message"]

    # 8. User attempts to login -> 404 "User not found."
    deleted_login = client.post(
        "/api/v1/auth/login",
        json={"username": test_user_name, "password": test_password},
    )
    assert deleted_login.status_code == 404
    assert deleted_login.json()["detail"] == "User not found."

    # 9. Admin inspects user -> is_deleted is True
    get_user = client.get(
        f"/api/v1/admin/users/{user_id}",
        cookies=admin_cookie,
    )
    assert get_user.status_code == 200
    assert get_user.json()["is_deleted"] is True
    assert get_user.json()["deleted_at"] is not None

    # 10. Admin cannot delete self via /admin/users/{id}
    me_res = client.get("/api/v1/admin/me", cookies=admin_cookie)
    admin_id = me_res.json()["id"]
    self_del = client.delete(f"/api/v1/admin/users/{admin_id}", cookies=admin_cookie)
    assert self_del.status_code == 400
    assert "Cannot delete your own account" in self_del.json()["detail"]


def test_admin_auth_endpoints(client: TestClient) -> None:
    # 1. Check existing username via /admin/auth/check-username
    res_taken = client.get("/api/v1/admin/auth/check-username", params={"username": "admin"})
    assert res_taken.status_code == 200
    assert res_taken.json()["available"] is False
    assert "already taken" in res_taken.json()["message"]

    # 2. Check available username via /admin/auth/check-username
    rand_name = f"newadm_{uuid.uuid4().hex[:6]}"
    res_avail = client.get("/api/v1/admin/auth/check-username", params={"username": rand_name})
    assert res_avail.status_code == 200
    assert res_avail.json()["available"] is True

    # 3. Login via /admin/auth/login
    login_res = client.post(
        "/api/v1/admin/auth/login",
        json={"username": "admin", "password": "password123"},
    )
    assert login_res.status_code == 200
    assert settings.COOKIE_NAME in login_res.cookies
    admin_cookie = {settings.COOKIE_NAME: login_res.cookies[settings.COOKIE_NAME]}

    # 4. Verify access to /admin/me with session
    me_res = client.get("/api/v1/admin/me", cookies=admin_cookie)
    assert me_res.status_code == 200
    assert me_res.json()["username"] == "admin"

    # 5. Logout via /admin/auth/logout
    logout_res = client.delete("/api/v1/admin/auth/logout")
    assert logout_res.status_code == 200
    assert "logged out successfully" in logout_res.json()["message"]


def test_openapi_schema(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]

    assert "/health" in paths
    assert "/api/v1/auth/check-username" in paths
    assert "/api/v1/auth/register" in paths
    assert "/api/v1/auth/login" in paths
    assert "/api/v1/me" in paths
    assert "/api/v1/admin/auth/check-username" in paths
    assert "/api/v1/admin/auth/login" in paths
    assert "/api/v1/admin/auth/logout" in paths
    assert "/api/v1/admin/me" in paths
    assert "/api/v1/admin/users" in paths
