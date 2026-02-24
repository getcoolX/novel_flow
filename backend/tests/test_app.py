import pytest


def test_health_endpoint() -> None:
    pytest.importorskip("fastapi")
    pytest.importorskip("fastapi.testclient")

    from fastapi.testclient import TestClient

    from backend.app import app

    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
