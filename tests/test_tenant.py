import uuid
from starlette.testclient import TestClient
from fastapi_starter_project.core.config import settings
from fastapi_starter_project.services.session_service import session_service


def get_admin_cookie(client: TestClient) -> dict[str, str]:
    login_res = client.post(
        "/platform/login",
        json={"email_or_username": "admin@example.com", "password": "password"},
    )
    assert login_res.status_code == 200
    assert settings.COOKIE_NAME in login_res.cookies
    return {settings.COOKIE_NAME: login_res.cookies[settings.COOKIE_NAME]}


def test_admin_login_and_logout(client: TestClient) -> None:
    # 1. Login with email
    login_res = client.post(
        "/platform/login",
        json={"email_or_username": "admin@example.com", "password": "password"},
    )
    assert login_res.status_code == 200
    assert settings.COOKIE_NAME in login_res.cookies

    # 2. Login with username
    login_user_res = client.post(
        "/platform/login",
        json={"email_or_username": "admin", "password": "password"},
    )
    assert login_user_res.status_code == 200

    # 3. Invalid credentials
    invalid_res = client.post(
        "/platform/login",
        json={"email_or_username": "admin", "password": "wrongpassword"},
    )
    assert invalid_res.status_code == 401

    # 4. Logout
    logout_res = client.delete("/platform/logout")
    assert logout_res.status_code == 200


def test_tenant_creation_and_lifecycle(client: TestClient) -> None:
    admin_cookie = get_admin_cookie(client)
    uid_suffix = uuid.uuid4().hex[:6]

    # 1. Validation error: passwords do not match
    bad_payload = {
        "name": f"Tenant {uid_suffix}",
        "phone_no": "9876543210",
        "email": f"tenant_{uid_suffix}@example.com",
        "address": "123 Main Road",
        "district": "Karur",
        "pincode": 639001,
        "is_verified": False,
        "is_active": True,
        "user_name": "Tenant Admin",
        "user_id_name": f"admin_{uid_suffix}",
        "user_email": f"tadmin_{uid_suffix}@example.com",
        "user_phone": "9876543211",
        "password": "password123",
        "confirm_password": "mismatchpassword",
    }
    fail_res = client.post("/platform/tenants", json=bad_payload, cookies=admin_cookie)
    assert fail_res.status_code == 422

    # 2. Valid tenant creation
    valid_payload = {**bad_payload, "confirm_password": "password123"}
    create_res = client.post("/platform/tenants", json=valid_payload, cookies=admin_cookie)
    assert create_res.status_code == 201
    tenant_data = create_res.json()
    tenant_id = tenant_data["id"]
    assert tenant_data["name"] == valid_payload["name"]
    assert tenant_data["is_active"] is True
    assert "password" not in tenant_data

    # 3. Get tenant details
    get_res = client.get(f"/platform/tenants/{tenant_id}", cookies=admin_cookie)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == tenant_id

    # 4. List tenants
    list_res = client.get("/platform/tenants", cookies=admin_cookie)
    assert list_res.status_code == 200
    assert any(t["id"] == tenant_id for t in list_res.json())

    # 5. Update tenant details
    update_res = client.put(
        f"/platform/tenants/{tenant_id}",
        json={"name": f"Updated Tenant {uid_suffix}", "district": "Coimbatore"},
        cookies=admin_cookie,
    )
    assert update_res.status_code == 200
    assert update_res.json()["name"] == f"Updated Tenant {uid_suffix}"
    assert update_res.json()["district"] == "Coimbatore"

    # 6. Patch tenant status: deactivate
    patch_res = client.patch(
        f"/platform/tenants/{tenant_id}",
        json={"is_active": False, "is_verified": True},
        cookies=admin_cookie,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["is_active"] is False
    assert patch_res.json()["is_verified"] is True

    # 7. Delete tenant
    del_res = client.delete(f"/platform/tenants/{tenant_id}", cookies=admin_cookie)
    assert del_res.status_code == 200


def test_tenant_user_management_and_sessions(client: TestClient) -> None:
    admin_cookie = get_admin_cookie(client)
    uid_suffix = uuid.uuid4().hex[:6]

    # 1. Create a tenant
    tenant_payload = {
        "name": f"Corp {uid_suffix}",
        "phone_no": "9876543210",
        "email": f"corp_{uid_suffix}@example.com",
        "address": "456 Tech Park",
        "district": "Chennai",
        "pincode": 600001,
        "is_verified": True,
        "is_active": True,
        "user_name": "Corp Admin",
        "user_id_name": f"corp_admin_{uid_suffix}",
        "user_email": f"corp_admin_{uid_suffix}@example.com",
        "user_phone": "9876543211",
        "password": "password123",
        "confirm_password": "password123",
    }
    t_res = client.post("/platform/tenants", json=tenant_payload, cookies=admin_cookie)
    assert t_res.status_code == 201
    tenant_id = t_res.json()["id"]

    # 2. Create another user under this tenant
    user_payload = {
        "name": "Jane Staff",
        "user_name": f"jane_{uid_suffix}",
        "email": f"jane_{uid_suffix}@example.com",
        "phone": "9876543299",
        "role": "tenant_user",
        "is_active": True,
        "password": "password123",
        "confirm_password": "password123",
    }
    user_res = client.post(
        f"/platform/tenants/{tenant_id}/users",
        json=user_payload,
        cookies=admin_cookie,
    )
    assert user_res.status_code == 201
    user_data = user_res.json()
    user_id = user_data["id"]
    assert user_data["user_name"] == f"jane_{uid_suffix}"
    assert user_data["role"] == "tenant_user"
    assert user_data["is_deleted"] is False

    # 3. List active users
    list_users = client.get(f"/platform/tenants/{tenant_id}/users", cookies=admin_cookie)
    assert list_users.status_code == 200
    assert any(u["id"] == user_id for u in list_users.json())

    # 4. Super admin updates user password or status
    patch_user = client.patch(
        f"/platform/tenants/{tenant_id}/users/{user_id}",
        json={"is_active": True, "password": "newpassword123", "confirm_password": "newpassword123"},
        cookies=admin_cookie,
    )
    assert patch_user.status_code == 200

    # 5. Get user details
    get_user = client.get(f"/platform/tenants/{tenant_id}/users/{user_id}", cookies=admin_cookie)
    assert get_user.status_code == 200
    assert get_user.json()["id"] == user_id

    # 6. Soft delete user
    del_res = client.delete(
        f"/platform/tenants/{tenant_id}/users/{user_id}",
        cookies=admin_cookie,
    )
    assert del_res.status_code == 200

    # 7. List deleted users
    deleted_list = client.get(
        f"/platform/tenants/{tenant_id}/users?deleted_users=true",
        cookies=admin_cookie,
    )
    assert deleted_list.status_code == 200
    deleted_ids = [u["id"] for u in deleted_list.json()]
    assert user_id in deleted_ids


import pytest

@pytest.mark.anyio
async def test_redis_session_service_lifecycle() -> None:
    u_id = uuid.uuid4()
    t_id = uuid.uuid4()
    session_id = await session_service.create_session(u_id, "tenant_user", t_id)
    assert await session_service.is_session_valid(session_id) is True

    # Invalidate session for user
    await session_service.invalidate_user_sessions(u_id)
    assert await session_service.is_session_valid(session_id) is False


def test_multi_role_authorization_matrix(client: TestClient) -> None:
    super_admin_cookie = get_admin_cookie(client)
    uid_suffix = uuid.uuid4().hex[:6]

    # --- 1. Platform Admin creates Platform User ---
    p_user_name = f"pusr_{uid_suffix}"
    client.post(
        "/platform/users",
        json={
            "username": p_user_name,
            "email": f"{p_user_name}@example.com",
            "full_name": "Platform User",
            "password": "password123",
            "role": "platform_user",
        },
        cookies=super_admin_cookie,
    )
    p_login = client.post(
        "/platform/login",
        json={"username": p_user_name, "password": "password123"},
    )
    p_user_cookie = {settings.COOKIE_NAME: p_login.cookies[settings.COOKIE_NAME]}

    # --- 2. Platform User creates Tenant A ---
    t_a_admin_user = f"tadmin_a_{uid_suffix}"
    t_a_payload = {
        "name": f"Tenant A {uid_suffix}",
        "phone_no": "9876543210",
        "email": f"ta_{uid_suffix}@example.com",
        "address": "Street A",
        "district": "District A",
        "pincode": 600001,
        "is_verified": True,
        "is_active": True,
        "user_name": "Admin Tenant A",
        "user_id_name": t_a_admin_user,
        "user_email": f"{t_a_admin_user}@example.com",
        "user_phone": "9876543211",
        "password": "password123",
        "confirm_password": "password123",
    }
    res_a = client.post("/platform/tenants", json=t_a_payload, cookies=p_user_cookie)
    assert res_a.status_code == 201
    tenant_a_id = res_a.json()["id"]

    # --- 3. Platform Admin creates Tenant B ---
    t_b_admin_user = f"tadmin_b_{uid_suffix}"
    t_b_payload = {
        "name": f"Tenant B {uid_suffix}",
        "phone_no": "9876543220",
        "email": f"tb_{uid_suffix}@example.com",
        "address": "Street B",
        "district": "District B",
        "pincode": 600002,
        "is_verified": True,
        "is_active": True,
        "user_name": "Admin Tenant B",
        "user_id_name": t_b_admin_user,
        "user_email": f"{t_b_admin_user}@example.com",
        "user_phone": "9876543221",
        "password": "password123",
        "confirm_password": "password123",
    }
    res_b = client.post("/platform/tenants", json=t_b_payload, cookies=super_admin_cookie)
    assert res_b.status_code == 201
    tenant_b_id = res_b.json()["id"]

    # --- 4. Login as Tenant A Admin ---
    t_a_login = client.post(
        "/platform/login",
        json={"username": t_a_admin_user, "password": "password123"},
    )
    assert t_a_login.status_code == 200
    t_a_cookie = {settings.COOKIE_NAME: t_a_login.cookies[settings.COOKIE_NAME]}

    # --- 5. Verify Platform User restrictions ---
    # Platform User CANNOT manage platform users
    p_users_denied = client.get("/platform/users", cookies=p_user_cookie)
    assert p_users_denied.status_code == 403

    # Platform User CAN manage Tenant A users
    p_manage_ta = client.get(f"/platform/tenants/{tenant_a_id}/users", cookies=p_user_cookie)
    assert p_manage_ta.status_code == 200

    # Platform User CAN manage Tenant B users
    p_manage_tb = client.get(f"/platform/tenants/{tenant_b_id}/users", cookies=p_user_cookie)
    assert p_manage_tb.status_code == 200

    # --- 6. Verify Tenant Admin capabilities & boundaries ---
    # Tenant Admin CANNOT access platform users
    ta_denied_platform = client.get("/platform/users", cookies=t_a_cookie)
    assert ta_denied_platform.status_code == 403

    # Tenant Admin CANNOT access tenants list/management
    ta_denied_tenants = client.get("/platform/tenants", cookies=t_a_cookie)
    assert ta_denied_tenants.status_code == 403

    # Tenant A Admin CAN manage users in Tenant A
    staff_user = f"staff_{uid_suffix}"
    staff_create = client.post(
        f"/platform/tenants/{tenant_a_id}/users",
        json={
            "name": "Staff A",
            "user_name": staff_user,
            "email": f"{staff_user}@example.com",
            "phone": "9876543255",
            "role": "tenant_user",
            "is_active": True,
            "password": "password123",
            "confirm_password": "password123",
        },
        cookies=t_a_cookie,
    )
    assert staff_create.status_code == 201
    staff_id = staff_create.json()["id"]

    # Tenant A Admin CANNOT manage users in Tenant B (Cross-tenant forbidden)
    cross_tenant_res = client.get(
        f"/platform/tenants/{tenant_b_id}/users",
        cookies=t_a_cookie,
    )
    assert cross_tenant_res.status_code == 403
    assert "You can only access resources within your own tenant" in cross_tenant_res.json()["detail"]

    # --- 7. Login as normal Tenant User (Staff A) ---
    staff_login = client.post(
        "/platform/login",
        json={"username": staff_user, "password": "password123"},
    )
    # Tenant user cannot login to admin panel
    assert staff_login.status_code == 403
