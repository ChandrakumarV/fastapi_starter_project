from typing import Generator
import pytest
from starlette.testclient import TestClient
from fastapi_starter_project.main import app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as test_client:
        yield test_client
