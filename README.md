# FastAPI Starter Project

A clean and modern starter template for building high-performance APIs with [FastAPI](https://fastapi.tiangolo.com/) and [uv](https://docs.astral.sh/uv/).

---

## 🚀 Features

- **FastAPI 0.143+** with standard extras (Uvicorn, Pydantic, Watchfiles).
- Managed with **uv** for ultra-fast dependency resolution and virtual environment management.
- Python 3.12+ support.
- Interactive OpenAPI documentation powered by Swagger UI and ReDoc.

---

## 📋 Prerequisites

- **Python**: `>= 3.12`
- **uv**: Modern Python package installer and runner ([Install uv](https://docs.astral.sh/uv/getting-started/installation/))

---

## 🛠️ Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/ChandrakumarV/fastapi_starter_project.git
cd fastapi_starter_project
```

### 2. Install Dependencies

Install all project dependencies into a local virtual environment:

```bash
uv sync
```

---

## 🏃 Running the Application

### Development Mode

Run the development server with live reload enabled:

```bash
uv run fastapi dev
```

The application will start at:
- **API Base URL**: `http://127.0.0.1:8000`
- **Interactive Swagger Docs**: `http://127.0.0.1:8000/docs`
- **Alternative ReDoc Docs**: `http://127.0.0.1:8000/redoc`

### Production Mode

Run the production server:

```bash
uv run fastapi run
```

---

## 📁 Project Structure

```text
fastapi_starter_project/
├── .python-version               # Pinned Python version (3.12)
├── pyproject.toml                # Project metadata and dependencies
├── uv.lock                       # Dependency lockfile
├── README.md                     # Project documentation
└── src/
    ├── main.py                   # FastAPI application instance & routes
    └── fastapi_starter_project/
        └── __init__.py           # Package initialization
```

---

## 🔌 API Endpoints

| Method | Path | Description |
| :--- | :--- | :--- |
| `GET` | `/` | Root endpoint returning a greeting message |
| `GET` | `/docs` | Swagger UI documentation |
| `GET` | `/redoc` | ReDoc documentation |

---

## 👤 Author

- **ChandrakumarV** - [chandrakumar252004@gmail.com](mailto:chandrakumar252004@gmail.com)
