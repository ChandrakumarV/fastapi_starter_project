# FastAPI Starter Project

A production-grade template for building high-performance APIs with [FastAPI](https://fastapi.tiangolo.com/), [SQLAlchemy 2.0](https://www.sqlalchemy.org/), [Alembic](https://alembic.sqlalchemy.org/), and [uv](https://docs.astral.sh/uv/).

---

## 🚀 Features

- **Clean Layered Architecture**: Modular separation of concerns (Core, Models, Schemas, Services, API Endpoints, Dependencies).
- **PostgreSQL Database**: Async database sessions powered by `SQLAlchemy 2.0` and `asyncpg`.
- **Database Migrations with Alembic**: Fully configured async schema migrations with autogenerate capabilities.
- **Cookie-Based JWT Authentication**: Secure HTTP-only cookies (`access_token`) with role management.
- **Type-Safe Configuration**: Strongly typed settings via `pydantic-settings` reading from `.env`.
- **Docker Compose**: Pre-configured PostgreSQL service ready for instant local development.
- **Automated Testing Suite**: Integration test suite using `pytest`.

---

## 📁 Project Structure

```text
fastapi_starter_project/
├── .env.example                          # Environment variables template
├── .env                                  # Local environment configuration (git-ignored)
├── .gitignore                            # Standard Python, uv, and environment ignores
├── docker-compose.yml                    # PostgreSQL container setup
├── alembic.ini                           # Alembic migration configuration
├── pyproject.toml                        # Project metadata, dependencies, scripts
├── uv.lock                               # Dependency lockfile
├── README.md                             # Documentation & Migration Guide
├── migrations/                           # Alembic migration files
│   ├── env.py                            # Async Alembic environment runner
│   └── versions/                         # Generated database migration scripts
├── src/
│   ├── main.py                           # App entrypoint shim for FastAPI CLI
│   └── fastapi_starter_project/
│       ├── __init__.py                   # Package exports and CLI runner
│       ├── main.py                       # App factory, lifespan, CORS, and routing
│       ├── core/
│       │   ├── config.py                 # Pydantic BaseSettings & connection URIs
│       │   ├── database.py               # Async engine, sessionmaker, and get_db dependency
│       │   ├── security.py               # JWT encoding/decoding and password verification
│       │   ├── dependencies.py           # Dependency injection (get_current_user)
│       │   └── init_db.py                # Database seeding script
│       ├── models/                       # SQLAlchemy ORM models
│       │   ├── base.py                   # Base declarative class
│       │   └── user.py                   # User database model
│       ├── schemas/                      # Pydantic validation schemas
│       │   ├── auth.py                   # Login & token payload schemas
│       │   ├── user.py                   # User response schemas
│       │   └── common.py                 # Health and generic message schemas
│       ├── services/                     # Business logic and database access layer
│       │   └── user_service.py           # User retrieval & authentication logic
│       └── api/
│           └── v1/
│               ├── router.py             # API v1 aggregator router
│               └── endpoints/
│                   ├── health.py         # Public /health endpoint
│                   ├── auth.py           # Public /login and /logout endpoints
│                   └── users.py          # Protected /me endpoint
└── tests/
    ├── conftest.py                       # Test fixtures and TestClient setup
    ├── test_health.py                    # Health check integration tests
    ├── test_auth.py                      # Auth & protected route tests
    └── test_db.py                        # Database connectivity tests
```

---

## 🛠️ Getting Started

### 1. Prerequisites

- **Python**: `>= 3.12`
- **uv**: Modern Python package installer ([Install uv](https://docs.astral.sh/uv/getting-started/installation/))
- **Docker**: For running the PostgreSQL database container

### 2. Environment Setup

Clone the repository and set up your `.env` file:

```bash
git clone https://github.com/ChandrakumarV/fastapi_starter_project.git
cd fastapi_starter_project

# Copy the environment file template
cp .env.example .env

# Install project dependencies
uv sync
```

---

## 🗄️ Database Setup (PostgreSQL)

The project is configured for PostgreSQL with the following default credentials:

| Variable | Value |
| :--- | :--- |
| `POSTGRES_SERVER` | `localhost` |
| `POSTGRES_PORT` | `5432` |
| `POSTGRES_USER` | `root` |
| `POSTGRES_PASSWORD` | `root` |
| `POSTGRES_DB` | `postgres` |

### Start PostgreSQL with Docker

You can spin up the PostgreSQL container in the background using `docker compose`:

```bash
# Start PostgreSQL container
docker compose up -d
```

*(Alternatively, if running standalone `docker run`:)*
```bash
docker run -d --name postgresql -p 5432:5432 -e POSTGRES_USER=root -e POSTGRES_PASSWORD=root -e POSTGRES_DB=postgres postgres:17-alpine
```

---

## 🔄 Database Migrations Guide (Alembic)

### What is a Migration?

When you modify your SQLAlchemy models in Python (for example, adding a new column or table), your database does not change automatically. 

**Migrations** act as **version control for your database**. Alembic inspects your Python models, compares them with the live database schema, generates a migration script with the difference, and applies those changes safely without losing data.

---

### Core Migration Commands Cheat Sheet

| Task | Command | Description |
| :--- | :--- | :--- |
| **Apply pending migrations** | `uv run alembic upgrade head` | Updates database schema to the latest version |
| **Create a new migration** | `uv run alembic revision --autogenerate -m "your_message"` | Generates a new migration script by detecting model changes |
| **Check current database version** | `uv run alembic current` | Displays the current revision applied to the database |
| **View migration history** | `uv run alembic history --verbose` | Lists all migrations in chronological order |
| **Rollback last migration** | `uv run alembic downgrade -1` | Undoes the single most recent migration |
| **Rollback completely** | `uv run alembic downgrade base` | Reverts all migrations back to an empty database |

---

### Step-by-Step Guide for Beginners

#### Step 1: Apply Initial Migrations

To apply existing migrations and create the tables in your PostgreSQL database:

```bash
uv run alembic upgrade head
```

#### Step 2: Seed Initial Data (Optional)

Populate default users (`admin` and `user`) into the `users` table:

```bash
uv run python src/fastapi_starter_project/core/init_db.py
```

#### Step 3: Making Changes to Database Models

Whenever you want to add a new table or modify a column:

1. **Edit or add your SQLAlchemy model** inside `src/fastapi_starter_project/models/` (e.g., adding `bio: Mapped[str] = mapped_column(String(255), nullable=True)` to `models/user.py`).
2. **Generate the migration script automatically**:
   ```bash
   uv run alembic revision --autogenerate -m "add bio to user model"
   ```
3. **Inspect the generated script** inside `migrations/versions/`. Alembic will have created a new Python file containing `upgrade()` and `downgrade()` functions.
4. **Apply the migration to PostgreSQL**:
   ```bash
   uv run alembic upgrade head
   ```
5. **Verify the change**:
   ```bash
   uv run alembic current
   ```

#### Step 4: Undoing a Mistake (Rollback)

If something went wrong with your latest migration:

```bash
# Revert the last applied migration
uv run alembic downgrade -1
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

### Production Mode

```bash
uv run fastapi run
```

---

## 🧪 Running Automated Tests

Run the full automated test suite (including health endpoints, auth flows, and database queries):

```bash
uv run pytest
```

---

## 🔌 API Endpoints Summary

### 1. System Health (Unversioned)

| Method | Path | Description | Access |
| :--- | :--- | :--- | :--- |
| `GET` | `/health` | Server status and PostgreSQL database connectivity | Public |
| `GET` | `/` | Redirects to Swagger UI documentation | Public |
| `GET` | `/docs` | Interactive Swagger UI | Public |
| `GET` | `/redoc` | Interactive ReDoc | Public |

### 2. Normal User Endpoints (Public & Protected)

| Method | Actual Path | Docs Display | Description | Access |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/auth/check-username` | `/auth/check-username` | Check if username is available (real-time) | Public |
| `POST` | `/api/v1/auth/register` | `/auth/register` | Self-registration (grants `user` role) | Public |
| `POST` | `/api/v1/auth/login` | `/auth/login` | Authenticate & issue HTTP-only JWT cookie | Public |
| `DELETE` | `/api/v1/auth/logout` | `/auth/logout` | Clear JWT authentication cookie | Public |
| `GET` | `/api/v1/me` | `/me` | Get currently logged-in user profile | Protected (`user` only) |
| `PUT` | `/api/v1/me` | `/me` | Update personal profile (name, email, password) | Protected (`user` only) |
| `DELETE` | `/api/v1/me` | `/me` | Delete own user account | Protected (`user` only) |

### 3. Admin Endpoints (`/admin` Prefix, Protected by `require_admin`)

| Method | Actual Path | Docs Display | Description | Access |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/admin/auth/check-username` | `/admin/auth/check-username` | Check username availability for admin | Public |
| `POST` | `/api/v1/admin/auth/login` | `/admin/auth/login` | Admin login (rejects non-admin users) | Public (checks admin role) |
| `DELETE` | `/api/v1/admin/auth/logout` | `/admin/auth/logout` | Clear admin session cookie | Public |
| `GET` | `/api/v1/admin/me` | `/admin/me` | Get current admin profile | Protected (`admin` only) |
| `PUT` | `/api/v1/admin/me` | `/admin/me` | Update current admin profile | Protected (`admin` only) |
| `DELETE` | `/api/v1/admin/me` | `/admin/me` | Soft delete current admin account | Protected (`admin` only) |
| `POST` | `/api/v1/admin/users` | `/admin/users` | Create new users with any role (`admin` or `user`) | Protected (`admin` only) |
| `GET` | `/api/v1/admin/users` | `/admin/users` | List all users in system (excluding deleted by default) | Protected (`admin` only) |
| `GET` | `/api/v1/admin/users/{user_id}` | `/admin/users/{user_id}` | Get user details by ID | Protected (`admin` only) |
| `PATCH` | `/api/v1/admin/users/{user_id}/status` | `/admin/users/{user_id}/status` | Activate or deactivate normal user (`{"is_active": bool}`) | Protected (`admin` only) |
| `DELETE` | `/api/v1/admin/users/{user_id}` | `/admin/users/{user_id}` | Soft delete user (sets `is_deleted=True` & `deleted_at`) | Protected (`admin` only) |

### 4. Account Lifecycle & Status Behavior

| State | `is_active` | `is_deleted` | Login Attempt Result |
| :--- | :--- | :--- | :--- |
| **Active** | `True` | `False` | `200 OK` (JWT issued) |
| **Inactive / Suspended** | `False` | `False` | `403 Forbidden` (`"Inactive user account. Please contact an administrator."`) |
| **Soft-Deleted** | Any | `True` | `404 Not Found` (`"User not found."`) |

---

## 🔑 Test Credentials (Default Database Users)

| Username | Password | Role | Allowed Endpoints |
| :--- | :--- | :--- | :--- |
| `admin` | `password123` | **admin** | All Admin (`/admin/...`) & User (`/...`) endpoints |
| `user` | `password456` | **user** | User endpoints (`/auth/login`, `/me`, etc.) |

---

## 👤 Author

- **ChandrakumarV** - [chandrakumar252004@gmail.com](mailto:chandrakumar252004@gmail.com)
