"""FastAPI Starter Project package."""
import uvicorn
from fastapi_starter_project.main import app


def main() -> None:
    """CLI entrypoint to run the server directly."""
    uvicorn.run("fastapi_starter_project.main:app", host="127.0.0.1", port=8000, reload=True)


__all__ = ["app", "main"]
