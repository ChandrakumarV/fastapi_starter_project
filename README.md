# FastAPI Starter Project

A production-grade template for building high-performance APIs with [FastAPI](https://fastapi.tiangolo.com/), [Pydantic v2](https://docs.pydantic.dev/), and [uv](https://docs.astral.sh/uv/).

---

## 🚀 Features

- **Production-grade Clean Architecture**: Layered separation of concerns (Core, Schemas, Services, API Endpoints, Dependencies).
- **Cookie-based JWT Authentication**: Secure HTTP-only cookies with JWT tokens (`access_token`).
- **Configuration with Pydantic Settings**: Strongly typed environment configurations from `.env` files via `pydantic-settings`.
- **API Versioning**: Structured versioned routing under `/api/v1` with convenient root aliases.
- **Dependency Injection**: Reusable dependencies for authentication and current user context.
- **Automated Testing Suite**: Full integration test coverage using `pytest` and `TestClient`.
- **Fast Package Management**: Managed with `uv` on Python 3.12+.

---

## 📁 Project Structure

```text
fastapi_starter_project/
├── .env.example                          # Environment variable template
├── .gitignore                            # Standard Python & uv gitignore
├── pyproject.toml                        # Project metadata, dependencies, scripts
├── uv.lock                               # Dependency lockfile
├── README.md                             # Documentation
├── src/
│   ├── main.py                           # App entrypoint shim
│   └── fastapi_starter_project/
│       ├── __init__.py                   # Package exports and CLI runner
│       ├── main.py                       # App factory, lifespan, CORS, and router assembly
│       ├── core/
│       │   ├── config.py                 # Pydantic BaseSettings & env parsing
│       │   ├── security.py               # JWT encoding/decoding and password hashing
│       │   └── dependencies.py           # Dependency injection (e.g., get_current_user)
│       ├── schemas/
│       │   ├── auth.py                   # Login & token payload schemas
│       │   ├── user.py                   # User request and response schemas
│       │   └── common.py                 # Health and generic message schemas
│       ├── services/
│       │   └── user_service.py           # Data access and business logic layer
│       └── api/
│           └── v1/
│               ├── router.py             # API v1 router aggregator
│               └── endpoints/
│                   ├── health.py         # Health check endpoint
│                   ├── auth.py           # Login and logout endpoints
│                   └── users.py          # Protected user endpoints
└── tests/
    ├── conftest.py                       # Test fixtures and TestClient setup
    ├── test_health.py                    # Health check integration tests
    └── test_auth.py                      # Authentication flow tests
```

---

## 🛠️ Getting Started

### 1. Prerequisites

- Python `>= 3.12`
- [uv package manager](https://docs.astral.sh/uv/getting-started/installation/)

### 2. Installation & Setup

```bash
# Clone the repository
git clone https://github.com/ChandrakumarV/fastapi_starter_project.git
cd fastapi_starter_project

# Copy the environment configuration
cp .env.example .env

# Install dependencies into virtual environment
uv sync
```

---

## 🏃 Running the Application

### Development Server

Run the development server with live reload:

```bash
uv run fastapi dev
```

The application will start at:
- **API Base URL**: `http://127.0.0.1:8000`
- **Interactive Swagger Docs**: `http://127.0.0.1:8000/docs`
- **Alternative ReDoc**: `http://127.0.0.1:8000/redoc`

### Production Server

Run the production server:

```bash
uv run fastapi run
```

---

## 🧪 Running Tests

Execute the automated test suite with `pytest`:

```bash
uv run pytest
```

---

## 🔌 API Endpoints

### Public Endpoints

| Method | Path | Description | Access |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | Redirects to `/docs` | Public |
| `GET` | `/health` or `/api/v1/health` | Health check & environment status | Public |
| `POST` | `/login` or `/api/v1/login` | Authenticate & issue HTTP-only JWT cookie | Public |
| `POST` | `/logout` or `/api/v1/logout` | Clear the JWT authentication cookie | Public |
| `GET` | `/docs` | Swagger UI documentation | Public |
| `GET` | `/redoc` | ReDoc documentation | Public |

### Protected Endpoints

| Method | Path | Description | Access |
| :--- | :--- | :--- | :--- |
| `GET` | `/me` or `/api/v1/me` | Fetch authenticated user profile | Protected (HTTP-only Cookie) |

---

## 🔑 Test Credentials (Dummy Store)

| Username | Password | Role |
| :--- | :--- | :--- |
| `johndoe` | `password123` | admin |
| `janedoe` | `password456` | user |

---

## 👤 Author

- **ChandrakumarV** - [chandrakumar252004@gmail.com](mailto:chandrakumar252004@gmail.com)
