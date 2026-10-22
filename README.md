# FastAPI Starter Project

A production-grade, multi-tenant backend built with [FastAPI](https://fastapi.tiangolo.com/), [SQLAlchemy 2.0](https://www.sqlalchemy.org/), [PostgreSQL](https://www.postgresql.org/), [Redis](https://redis.io/), [Alembic](https://alembic.sqlalchemy.org/), and [uv](https://docs.astral.sh/uv/).

---

## 🚀 Features

- **Multi-Tenant Architecture**: Strict tenant data isolation with dedicated tenant entities and scoped user administration.
- **Hierarchical Role-Based Access Control (RBAC)**: Fine-grained permissions cleanly distinguishing Platform Admins, Platform Users, Tenant Admins, and Tenant Users.
- **Sub-Millisecond Redis Session Caching**: Requests are authenticated directly from Redis memory in ~0.2ms, completely eliminating redundant PostgreSQL lookups on every single request.
- **Instant Session Invalidation**: Immediate session termination across user profile edits, password resets, soft deletes, and tenant deactivations.
- **PostgreSQL Database**: High-performance asynchronous database operations powered by `SQLAlchemy 2.0` and `asyncpg` with secure UUID primary keys.
- **Alembic Database Migrations**: Fully configured async schema migrations with automated generation capabilities.
- **Cookie & Bearer Token Authentication**: Dual-mode authentication supporting secure HTTP-only cookies (`access_token`) and `Authorization: Bearer <token>` headers.
- **Docker Compose**: Pre-configured multi-container environment with PostgreSQL and Redis for instant local development.
- **Automated Testing Suite**: Full integration test suite using `pytest` and `anyio`.

---

## 👥 Role Hierarchy & Authorization Matrix

The platform defines four standard user roles in `fastapi_starter_project.models.enums.UserRole`:

| Role | Description | Scope |
| :--- | :--- | :--- |
| **`platform_admin`** | Top-level platform administrator. Full system and platform user control. | Global |
| **`platform_user`** | Platform operator staff user. Manages tenants and tenant users across the platform. | Global |
| **`tenant_admin`** | Administrator of a specific tenant organization. Manages users within their assigned tenant. | Tenant-Scoped |
| **`tenant_user`** | Standard member of a tenant organization. | Tenant-Scoped |

### Access Control Matrix

| Resource / Endpoint | `platform_admin` | `platform_user` | `tenant_admin` | `tenant_user` |
| :--- | :---: | :---: | :---: | :---: |
| **Platform Users** (`/platform/users`) | ✅ Full Access | ❌ Forbidden (403) | ❌ Forbidden (403) | ❌ Forbidden (403) |
| **Tenants** (`/platform/tenants`) | ✅ Full Access | ✅ Full Access | ❌ Forbidden (403) | ❌ Forbidden (403) |
| **Tenant Users** (`/platform/tenants/{id}/users`) | ✅ Full Access | ✅ Full Access | ✅ Own Tenant Only | ❌ Forbidden (403) |
| **Platform Login** (`/platform/login`) | ✅ Allowed | ✅ Allowed | ✅ Allowed | ❌ Forbidden (403) |
| **Platform Me** (`/platform/me`) | ✅ Allowed | ✅ Allowed | ❌ Forbidden (403) | ❌ Forbidden (403) |

> [!NOTE]
> - **Platform Users**: Can **only** be managed by `platform_admin`.
> - **Tenants & Tenant Users**: Can be managed by both `platform_admin` and `platform_user`.
> - **Tenant Admins**: Can manage tenant users **strictly within their own tenant**. Cross-tenant management is forbidden (403).

---

## 📁 Project Structure

```text
fastapi_starter_project/
├── .env.example                          # Environment variables template
├── .env                                  # Local environment configuration (git-ignored)
├── docker-compose.yml                    # PostgreSQL & Redis container setup
├── alembic.ini                           # Alembic migration configuration
├── pyproject.toml                        # Project metadata, dependencies, scripts
├── uv.lock                               # Dependency lockfile
├── README.md                             # Documentation
├── migrations/                           # Alembic database migrations
│   ├── env.py                            # Async migration runner
│   └── versions/                         # Versioned migration scripts
├── src/
│   ├── main.py                           # App entrypoint shim for FastAPI CLI
│   └── fastapi_starter_project/
│       ├── main.py                       # App factory, lifespan, CORS, and routing
│       ├── core/
│       │   ├── config.py                 # Pydantic BaseSettings & connection URIs
│       │   ├── database.py               # Async engine, sessionmaker, and get_db dependency
│       │   ├── redis.py                  # Async Redis connection pool and client
│       │   ├── security.py               # JWT encoding/decoding and PBKDF2 password hashing
│       │   ├── dependencies.py           # Dependency injection & RBAC validators
│       │   └── init_db.py                # Database seeding script
│       ├── models/                       # SQLAlchemy ORM models
│       │   ├── base.py                   # Declarative base class
│       │   ├── enums.py                  # UserRole enum definitions
│       │   ├── tenant.py                 # Tenant model
│       │   └── user.py                   # User model (with tenant relationships & audit fields)
│       ├── schemas/                      # Pydantic validation schemas
│       │   ├── common.py                 # Health and generic message schemas
│       │   ├── tenant.py                 # Tenant create, update, patch, and response schemas
│       │   ├── tenant_user.py            # Tenant user management schemas
│       │   └── user.py                   # Platform user & admin schemas
│       ├── services/                     # Business logic and database access layer
│       │   ├── session_service.py        # Redis session tracking and invalidation
│       │   ├── tenant_service.py         # Multi-tenant operations & lifecycle logic
│       │   └── user_service.py           # User management and authentication logic
│       └── api/
│           └── v1/
│               ├── endpoints/
│               │   ├── health.py         # Public /health endpoint
│               │   └── platform/         # Platform endpoints (/platform/...)
│               │       ├── auth.py       # /platform/login, /platform/logout
│               │       ├── me.py         # /platform/me profile management
│               │       ├── users.py      # /platform/users platform admin/user management
│               │       ├── tenants.py    # /platform/tenants tenant management
│               │       └── tenant_users.py # /platform/tenants/{id}/users user management
│               └── router.py             # API router aggregator
└── tests/
    ├── conftest.py                       # Test fixtures and TestClient setup
    ├── test_health.py                    # Health check integration tests
    ├── test_admin.py                     # Platform admin & auth tests
    ├── test_tenant.py                    # Multi-tenant & multi-role authorization tests
    └── test_db.py                        # Database connectivity tests
```

---

## 🛠️ Getting Started

### 1. Prerequisites

- **Python**: `>= 3.12`
- **uv**: Fast Python package manager ([Install uv](https://docs.astral.sh/uv/getting-started/installation/))
- **Docker**: For running PostgreSQL and Redis containers

### 2. Environment Setup

```bash
# Clone the repository
git clone https://github.com/ChandrakumarV/fastapi_starter_project.git
cd fastapi_starter_project

# Copy the environment file template
cp .env.example .env

# Install project dependencies
uv sync
```

---

## 🗄️ Database & Services (PostgreSQL & Redis)

Start PostgreSQL and Redis in the background using `docker compose`:

```bash
docker compose up -d
```

### Apply Migrations

```bash
uv run alembic upgrade head
```

### Seed Initial Data

Populates the default platform admin, an initial tenant (`ABC Exports`), a tenant administrator, and a tenant user:

```bash
uv run python -c "import sys; sys.path.insert(0, 'src'); from fastapi_starter_project.core.init_db import seed_initial_data; import asyncio; asyncio.run(seed_initial_data())"
```

---

## 🏃 Running the Application

### Development Mode (with Live Reload)

```bash
uv run fastapi dev
```

The application will be accessible at:
- **API Base**: `http://127.0.0.1:8000`
- **Interactive Swagger Docs**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`

---

## 🧪 Running Automated Tests

Run the full integration test suite:

```bash
uv run pytest
```

---

## 🔌 API Endpoints Summary

### 1. System Health

| Method | Path | Description | Access |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | Server status and database connectivity | Public |
| `GET` | `/` | Redirects to Swagger UI documentation | Public |
| `GET` | `/docs` | Interactive Swagger UI | Public |
| `GET` | `/redoc` | Interactive ReDoc | Public |

### 2. Platform Authentication (`/platform`)

| Method | Path | Description | Access |
| :--- | :--- | :--- | :--- |
| `POST` | `/platform/login` | Authenticates administrator credentials and sets an HTTP-only JWT cookie with cached session | Public (`platform_admin`, `platform_user`, `tenant_admin`) |
| `DELETE` | `/platform/logout` | Clears the JWT authentication cookie and revokes session | Public |
| `GET` | `/platform/me` | Fetches currently authenticated platform profile | Protected (`require_platform_access`) |
| `PUT` | `/platform/me` | Updates current platform user profile | Protected (`require_platform_access`) |
| `DELETE` | `/platform/me` | Soft deletes current platform user account | Protected (`require_platform_access`) |

### 3. Platform Users (`/platform/users`)

| Method | Path | Description | Access |
| :--- | :--- | :--- | :--- |
| `POST` | `/platform/users` | Create platform accounts (`platform_admin` or `platform_user`) | `platform_admin` only |
| `GET` | `/platform/users` | List platform admin users | `platform_admin` only |
| `GET` | `/platform/users/{user_id}` | Get platform admin user details | `platform_admin` only |
| `PATCH` | `/platform/users/{user_id}/status` | Activate or deactivate platform accounts | `platform_admin` only |
| `DELETE` | `/platform/users/{user_id}` | Soft delete platform accounts | `platform_admin` only |

### 4. Tenants (`/platform/tenants`)

| Method | Path | Description | Access |
| :--- | :--- | :--- | :--- |
| `POST` | `/platform/tenants` | Create tenant and provision initial tenant administrator atomically | `platform_admin`, `platform_user` |
| `GET` | `/platform/tenants` | List active tenants (paginated) | `platform_admin`, `platform_user` |
| `GET` | `/platform/tenants/{tenant_id}` | Get tenant details | `platform_admin`, `platform_user` |
| `PUT` | `/platform/tenants/{tenant_id}` | Update tenant details | `platform_admin`, `platform_user` |
| `PATCH` | `/platform/tenants/{tenant_id}` | Update tenant active status or verification (deactivation invalidates tenant sessions) | `platform_admin`, `platform_user` |
| `DELETE` | `/platform/tenants/{tenant_id}` | Soft delete tenant and invalidate all tenant user sessions | `platform_admin`, `platform_user` |

### 5. Tenant Users (`/platform/tenants/{tenant_id}/users`)

| Method | Path | Description | Access |
| :--- | :--- | :--- | :--- |
| `POST` | `/platform/tenants/{tenant_id}/users` | Provision new user or administrator within tenant | `platform_admin`, `platform_user`, or `tenant_admin` (own tenant) |
| `GET` | `/platform/tenants/{tenant_id}/users` | List active users in tenant (`?deleted_users=true` for deleted) | `platform_admin`, `platform_user`, or `tenant_admin` (own tenant) |
| `GET` | `/platform/tenants/{tenant_id}/users/{user_id}` | Get tenant user details | `platform_admin`, `platform_user`, or `tenant_admin` (own tenant) |
| `PUT` | `/platform/tenants/{tenant_id}/users/{user_id}` | Update tenant user profile (revokes active sessions) | `platform_admin`, `platform_user`, or `tenant_admin` (own tenant) |
| `PATCH` | `/platform/tenants/{tenant_id}/users/{user_id}` | Change user password or status (revokes active sessions) | `platform_admin`, `platform_user`, or `tenant_admin` (own tenant) |
| `DELETE` | `/platform/tenants/{tenant_id}/users/{user_id}` | Soft delete user and revoke all active sessions | `platform_admin`, `platform_user`, or `tenant_admin` (own tenant) |

---

## ⚡ Redis Session Caching & Invalidation Architecture

### Fast-Path Caching (Sub-Millisecond Auth)
When an administrator logs in, a session payload is generated and saved in Redis under `session:{session_id}` storing the user's ID, username, email, role, and tenant metadata. On every incoming request:
1. The JWT is validated in memory.
2. The active session payload is retrieved from Redis in **~0.2ms**.
3. The user representation is instantiated directly **without executing SQL queries against PostgreSQL**.

### Instant Invalidation
Because active sessions live in Redis, any security event invalidates the session keys immediately:
1. **User Logout**: Deletes `session:{session_id}`.
2. **Password Change or Profile Update**: Invokes `session_service.invalidate_user_sessions(user_id)`.
3. **User Deactivation / Soft-Deletion**: Immediately revokes all active sessions for that user.
4. **Tenant Deactivation / Soft-Deletion**: Invokes `session_service.invalidate_tenant_sessions(tenant_id)`, revoking sessions across every user in the tenant organization.

---

## 🔑 Default Seed Credentials

After running database seed:

| Username | Password | Role | Scope |
| :--- | :--- | :--- | :--- |
| `admin` | `password123` | `platform_admin` | Global Platform Admin |
| `abc_admin` | `password` | `tenant_admin` | Tenant Admin (`ABC Exports`) |
| `abc_user` | `password` | `tenant_user` | Tenant User (`ABC Exports`) |

---

## 👤 Author

- **ChandrakumarV** - [chandrakumar252004@gmail.com](mailto:chandrakumar252004@gmail.com)
