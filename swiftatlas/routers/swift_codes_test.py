import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    from swiftatlas.main import app

    return TestClient(app)
