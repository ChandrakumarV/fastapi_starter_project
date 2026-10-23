# Tenant-Based User Management & Session Handling

## 1. User Roles and Permissions

| Role                   | Permissions                                        |
| ---------------------- | -------------------------------------------------- |
| `platform_admin` | Manage tenants and all tenant users.               |
| `tenant_admin`         | Manage users within their own tenant.              |
| `tenant_user`          | Access permitted features within their own tenant. |

## 2. Session Management (Redis + JWT)

Session management applies only to `tenant_admin` and `tenant_user`. The `platform_admin` does not use Redis-backed session validation.

### Login flow

1. Validate the user's credentials.
2. Generate a unique `session_id`.
3. Include the `session_id` in the JWT payload.
4. Store the session in Redis, keyed by `session_id`.
5. Return the JWT to the client.

### Request authentication flow

1. Validate the JWT signature and expiration.
2. Extract the user's role and `session_id`.
3. If the role is `tenant_admin` or `tenant_user`, check whether the session exists in Redis.
4. If the session does not exist, reject the request.
5. If the session exists, continue authorization and request processing.
6. HTTP only cookie based authentication.

Recommended: Return `401 Unauthorized` for missing or invalid sessions rather than `404 Not Found`.

### Session invalidation

Remove the user's active Redis session(s) whenever:

- A user's name, username, password, or account status changes.
- A user deletes their own account or is deleted by an authorized administrator.
- A tenant is deleted.
- A tenant's `is_active` status changes to `false`.

These rules apply to changes made by `platform_admin`, `tenant_admin`, or the affected user, subject to their permissions.

When a tenant is deactivated or deleted, invalidate sessions for all users belonging to that tenant.

## 3. Platform Super Admin APIs

Base prefix: `/admin`

### 3.1 Authentication

| Method   | Endpoint        | Description                            |
| -------- | --------------- | -------------------------------------- |
| `POST`   | `/admin/login`  | Authenticate the platform super admin. |
| `DELETE` | `/admin/logout` | Log out the platform super admin.      |

Login request

```json
{
  "username": "admin",
  "password": "password"
}
```

The platform super admin does not require Redis-backed session validation. Logout should invalidate the token using an appropriate strategy if immediate token revocation is required.

### 3.2 Tenant management

| Method   | Endpoint                     | Description                                         |
| -------- | ---------------------------- | --------------------------------------------------- |
| `GET`    | `/admin/tenants`             | List tenants.                                       |
| `GET`    | `/admin/tenants/{tenant_id}` | Get tenant details.                                 |
| `POST`   | `/admin/tenants`             | Create a tenant and its first tenant admin.         |
| `PUT`    | `/admin/tenants/{tenant_id}` | Update tenant details.                              |
| `PATCH`  | `/admin/tenants/{tenant_id}` | Update tenant status or verification.               |
| `DELETE` | `/admin/tenants/{tenant_id}` | Delete a tenant and invalidate its users' sessions. |

Create tenant request

```
{
  "name": "ABC Exports",
  "phone_no": "9876543210",
  "email": "contact@example.com",
  "address": "123 Main Road",
  "district": "Karur",
  "pincode": 639001,
  "is_verified": false,
  "is_active": true,
  "full_name": "Tenant Admin",
  "user_name": "abc_admin",
  "user_email": "admin@example.com",
  "user_phone": "9876543211",
  "password": "password",
  "confirm_password": "password"
}
```

Notes:

- `user_name` is the tenant admin's unique username in the database.
- Validate password confirmation on the server.
- Hash passwords before storing them.
- Create the tenant and its first admin in a single database transaction.

Tenant response fields

```
{
  "id": "uuid",
  "created_at": "2026-10-22T10:00:00Z",
  "name": "ABC Exports",
  "phone_no": "9876543210",
  "email": "contact@example.com",
  "address": "123 Main Road",
  "district": "Karur",
  "pincode": 639001,
  "is_verified": false,
  "is_active": true
}
```

Do not return `password` or `confirm_password` in API responses.

For `PATCH /admin/tenants/{tenant_id}`, accept one or both of the following fields:

```
{
  "is_active": false
}
```

```
{
  "is_verified": true
}
```

If `is_active` becomes `false`, invalidate all sessions belonging to the tenant.

### 3.3 Tenant user management

These endpoints allow `platform_admin` to manage users within any tenant.

| Method   | Endpoint                                              | Description                        |
| -------- | ----------------------------------------------------- | ---------------------------------- |
| `GET`    | `/admin/tenants/{tenant_id}/users`                    | List active/non-deleted users.     |
| `GET`    | `/admin/tenants/{tenant_id}/users?deleted_users=true` | List deleted users.                |
| `GET`    | `/admin/tenants/{tenant_id}/users/{user_id}`          | Get user details.                  |
| `POST`   | `/admin/tenants/{tenant_id}/users`                    | Create a tenant user.              |
| `PUT`    | `/admin/tenants/{tenant_id}/users/{user_id}`          | Update user details.               |
| `PATCH`  | `/admin/tenants/{tenant_id}/users/{user_id}`          | Update password or account status. |
| `DELETE` | `/admin/tenants/{tenant_id}/users/{user_id}`          | Delete a user.                     |

Create user request

```
{
  "full_name": "John Doe",
  "user_name": "john_doe",
  "email": "john@example.com",
  "phone": "9876543212",
  "role": "tenant_admin | tenant_user",
  "is_active": true,
  "password": "password",
  "confirm_password": "password"
}
```

Update user request

```
{
  "full_name": "John Smith",
  "user_name": "john_smith",
  "email": "john.smith@example.com",
  "phone": "9876543213",
  "role": "tenant_admin | tenant_user",
}
```

Update password

```
{
  "password": "new_password",
  "confirm_password": "new_password"
}
```

Update account status

```
{
  "is_active": false
}
```

For the `PATCH` endpoint, validate which fields are provided and process the appropriate update. Invalidate the affected user's sessions after password or account status changes.

### 3.4 Tenant user response

```
{
  "id": "uuid",
  "created_at": "2026-10-22T10:00:00Z",
  "created_by": {
    "id": "uuid",
    "name": "Platform Admin"
  },
  "full_name": "John Doe",
  "user_name": "john_doe",
  "email": "john@example.com",
  "phone": "9876543212",
  "role": "tenant_admin | tenant_user",
  "is_active": true,
  "is_deleted": false,
  "deleted_at": null,
  "deleted_by": null
}
```

For deleted-user listings, include `deleted_at` and `deleted_by`. Prefer soft deletion if deleted users must remain available for audit purposes.

## 4. Tenant Admin APIs

Base prefix: `/tenant`

Tenant admins can manage only users belonging to their own tenant.

| Method   | Endpoint                  | Description                        |
| -------- | ------------------------- | ---------------------------------- |
| `GET`    | `/tenant/users`           | List users in the current tenant.  |
| `GET`    | `/tenant/users/{user_id}` | Get user details.                  |
| `POST`   | `/tenant/users`           | Create a tenant user.              |
| `PUT`    | `/tenant/users/{user_id}` | Update user details.               |
| `PATCH`  | `/tenant/users/{user_id}` | Update password or account status. |
| `DELETE` | `/tenant/users/{user_id}` | Delete a user.                     |

Reuse the same request and response schemas as the platform super admin's tenant-user endpoints where appropriate.

Authorization requirements:

- A tenant admin cannot manage users belonging to another tenant.
- A tenant admin cannot create or promote a user to `platform_admin` or `tenant_admin`.
- Tenant IDs must be derived from the authenticated user's identity, not trusted from client input.
- A tenant user cannot access user-management endpoints unless explicitly authorized.

## 5. Important Implementation Rules

1. Use role-based access control (RBAC) for every protected endpoint.
2. Enforce tenant isolation in database queries, not just in frontend checks.
3. Use Redis session keys with a TTL aligned to the JWT/session expiration.
4. Invalidate all sessions for the affected user when credentials or access status change.
5. Invalidate all tenant sessions when the tenant is deactivated or deleted.
6. Use soft deletion and audit fields if deleted-user history is required.
7. Use database transactions when creating a tenant and its first admin.
8. Never expose passwords or password confirmation fields in responses.
9. Validate uniqueness for usernames and any globally unique email fields.
10. Use `401` for unauthenticated requests and `403` for authenticated users without permission. Use `404` when a resource does not exist or when you intentionally conceal cross-tenant resources.

One additional design detail: if users can have multiple simultaneous logins, store a distinct session per login. On user updates or deletion, remove every session associated with that user, rather than only the most recent session.
