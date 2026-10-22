import uuid
from starlette.testclient import TestClient
from fastapi_starter_project.core.config import settings


def test_platform_login_rejects_non_platform_roles(client: TestClient) -> None:
    # 1. abc_user is a normal tenant user (role='tenant_user')
    res_user = client.post(
        "/platform/login",
        json={"username": "abc_user", "password": "password"},
    )
    assert res_user.status_code == 403
    assert "Platform privileges required" in res_user.json()["detail"]

    # 2. abc_admin is a tenant admin (role='tenant_admin') - must also be rejected from /platform/login
    res_admin = client.post(
        "/platform/login",
        json={"username": "abc_admin", "password": "password"},
    )
    assert res_admin.status_code == 403
    assert "Platform privileges required" in res_admin.json()["detail"]


def test_platform_flow_and_me_crud(client: TestClient) -> None:
    # 1. Login with seeded admin 'admin'
    login_response = client.post(
        "/platform/login",
        json={"username": "admin", "password": "password123"},
    )
    assert login_response.status_code == 200
    assert settings.COOKIE_NAME in login_response.cookies
    admin_cookie = {settings.COOKIE_NAME: login_response.cookies[settings.COOKIE_NAME]}

    # 2. GET /platform/me (allowed for platform admin)
    me_res = client.get("/platform/me", cookies=admin_cookie)
    assert me_res.status_code == 200
    assert me_res.json()["username"] == "admin"
    assert me_res.json()["role"] == "platform_admin"

    # 3. PUT /platform/me (update profile)
    put_res = client.put(
        "/platform/me",
        json={"full_name": "John Doe Senior"},
        cookies=admin_cookie,
    )
    assert put_res.status_code == 200
    assert put_res.json()["full_name"] == "John Doe Senior"

    # 4. Platform Admin creates a platform user
    new_user_username = f"puser_{uuid.uuid4().hex[:6]}"
    create_res = client.post(
        "/platform/users",
        json={
            "username": new_user_username,
            "email": f"{new_user_username}@example.com",
            "full_name": "New Platform User",
            "password": "seconduserpassword",
            "role": "platform_user",
        },
        cookies=admin_cookie,
    )
    assert create_res.status_code == 201
    assert create_res.json()["username"] == new_user_username
    assert create_res.json()["role"] == "platform_user"

    # 5. Platform Admin lists all users
    list_res = client.get("/platform/users", cookies=admin_cookie)
    assert list_res.status_code == 200
    usernames = [u["username"] for u in list_res.json()]
    assert "admin" in usernames
    assert new_user_username in usernames

    # 6. DELETE /platform/logout
    logout_res = client.delete("/platform/logout")
    assert logout_res.status_code == 200


def test_platform_me_denied_for_normal_user(client: TestClient) -> None:
    from fastapi_starter_project.core.security import create_access_token

    # Token for normal non-platform user
    token = create_access_token(subject="abc_user", role="user")
    user_cookie = {settings.COOKIE_NAME: token}

    # Attempt to access GET /platform/me
    admin_get = client.get("/platform/me", cookies=user_cookie)
    assert admin_get.status_code == 403
    assert admin_get.json()["detail"] == "Platform access required."

    # Attempt to access PUT /platform/me
    admin_put = client.put(
        "/platform/me",
        json={"full_name": "User Impersonating Admin"},
        cookies=user_cookie,
    )
    assert admin_put.status_code == 403
    assert admin_put.json()["detail"] == "Platform access required."

    # Attempt to access DELETE /platform/me
    admin_del = client.delete("/platform/me", cookies=user_cookie)
    assert admin_del.status_code == 403
    assert admin_del.json()["detail"] == "Platform access required."

    # Attempt to access GET /platform/users
    admin_users = client.get("/platform/users", cookies=user_cookie)
    assert admin_users.status_code == 403


def test_platform_toggle_user_active_and_soft_delete(client: TestClient) -> None:
    # 1. Admin login
    admin_login = client.post(
        "/platform/login",
        json={"username": "admin", "password": "password123"},
    )
    assert admin_login.status_code == 200
    admin_cookie = {settings.COOKIE_NAME: admin_login.cookies[settings.COOKIE_NAME]}

    # 2. Admin creates a platform user
    uid = uuid.uuid4().hex[:6]
    test_user_name = f"puser_{uid}"
    test_password = "password123"
    create_res = client.post(
        "/platform/users",
        json={
            "username": test_user_name,
            "email": f"{test_user_name}@example.com",
            "full_name": "Test Platform User",
            "password": test_password,
            "role": "platform_user",
        },
        cookies=admin_cookie,
    )
    assert create_res.status_code == 201
    user_id = create_res.json()["id"]

    # 3. Admin deactivates user
    deactivate_res = client.patch(
        f"/platform/users/{user_id}/status",
        json={"is_active": False},
        cookies=admin_cookie,
    )
    assert deactivate_res.status_code == 200
    assert deactivate_res.json()["is_active"] is False

    # 4. User attempts to login -> 403 Inactive account
    inactive_login = client.post(
        "/platform/login",
        json={"username": test_user_name, "password": test_password},
    )
    assert inactive_login.status_code == 403
    assert "Inactive admin account" in inactive_login.json()["detail"]

    # 5. Admin reactivates user
    reactivate_res = client.patch(
        f"/platform/users/{user_id}/status",
        json={"is_active": True},
        cookies=admin_cookie,
    )
    assert reactivate_res.status_code == 200
    assert reactivate_res.json()["is_active"] is True

    # 6. User logs in successfully
    active_login = client.post(
        "/platform/login",
        json={"username": test_user_name, "password": test_password},
    )
    assert active_login.status_code == 200

    # 7. Admin soft-deletes user
    del_res = client.delete(
        f"/platform/users/{user_id}",
        cookies=admin_cookie,
    )
    assert del_res.status_code == 200
    assert "deleted successfully" in del_res.json()["message"]

    # 8. User attempts to login -> 404 "User not found."
    deleted_login = client.post(
        "/platform/login",
        json={"username": test_user_name, "password": test_password},
    )
    assert deleted_login.status_code == 404
    assert deleted_login.json()["detail"] == "User not found."

    # 9. Admin inspects user -> is_deleted is True
    get_user = client.get(
        f"/platform/users/{user_id}",
        cookies=admin_cookie,
    )
    assert get_user.status_code == 200
    assert get_user.json()["is_deleted"] is True
    assert get_user.json()["deleted_at"] is not None

    # 10. Admin cannot delete self via /platform/users/{id}
    me_res = client.get("/platform/me", cookies=admin_cookie)
    admin_id = me_res.json()["id"]
    self_del = client.delete(f"/platform/users/{admin_id}", cookies=admin_cookie)
    assert self_del.status_code == 400
    assert "Cannot delete your own account" in self_del.json()["detail"]


def test_platform_auth_endpoints(client: TestClient) -> None:
    # 1. Login via /platform/login
    login_res = client.post(
        "/platform/login",
        json={"username": "admin", "password": "password123"},
    )
    assert login_res.status_code == 200
    assert settings.COOKIE_NAME in login_res.cookies
    admin_cookie = {settings.COOKIE_NAME: login_res.cookies[settings.COOKIE_NAME]}

    # 2. Verify access to /platform/me with session
    me_res = client.get("/platform/me", cookies=admin_cookie)
    assert me_res.status_code == 200
    assert me_res.json()["username"] == "admin"

    # 3. Logout via /platform/logout
    logout_res = client.delete("/platform/logout")
    assert logout_res.status_code == 200
    assert "logged out successfully" in logout_res.json()["message"]


def test_openapi_schema(client: TestClient) -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    paths = response.json()["paths"]

    assert "/health" in paths
    assert "/platform/login" in paths
    assert "/platform/logout" in paths
    assert "/platform/me" in paths
    assert "/platform/users" in paths
    assert "/platform/tenants" in paths


def test_platform_user_role_restrictions(client: TestClient) -> None:
    # 1. Login as seeded platform admin
    login_res = client.post(
        "/platform/login",
        json={"username": "admin", "password": "password123"},
    )
    assert login_res.status_code == 200
    admin_cookie = {settings.COOKIE_NAME: login_res.cookies[settings.COOKIE_NAME]}

    # 2. Reject creating invalid role in /platform/users
    invalid_role_res = client.post(
        "/platform/users",
        json={
            "username": f"bad_{uuid.uuid4().hex[:6]}",
            "email": f"bad_{uuid.uuid4().hex[:6]}@example.com",
            "full_name": "Bad Role User",
            "password": "password123",
            "role": "tenant_user",
        },
        cookies=admin_cookie,
    )
    assert invalid_role_res.status_code == 422

    # 3. Create a valid platform_user
    p_user_username = f"pusr_{uuid.uuid4().hex[:6]}"
    p_user_res = client.post(
        "/platform/users",
        json={
            "username": p_user_username,
            "email": f"{p_user_username}@example.com",
            "full_name": "Platform User One",
            "password": "securepassword",
            "role": "platform_user",
        },
        cookies=admin_cookie,
    )
    assert p_user_res.status_code == 201
    assert p_user_res.json()["role"] == "platform_user"

    # 4. Login as newly created platform_user
    p_login = client.post(
        "/platform/login",
        json={"username": p_user_username, "password": "securepassword"},
    )
    assert p_login.status_code == 200
    p_cookie = {settings.COOKIE_NAME: p_login.cookies[settings.COOKIE_NAME]}

    # 5. Platform user can access /platform/me
    p_me = client.get("/platform/me", cookies=p_cookie)
    assert p_me.status_code == 200
    assert p_me.json()["role"] == "platform_user"

    # 6. Platform user CANNOT manage platform users (only platform admin can)
    p_users = client.get("/platform/users", cookies=p_cookie)
    assert p_users.status_code == 403
    assert p_users.json()["detail"] == "Platform admin privileges required."

    # 7. Platform user CAN manage tenants
    p_tenants = client.get("/platform/tenants", cookies=p_cookie)
    assert p_tenants.status_code == 200
