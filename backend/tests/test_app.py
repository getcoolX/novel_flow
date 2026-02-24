import importlib.util

import pytest

HAS_FASTAPI = importlib.util.find_spec("fastapi") is not None
pytestmark = pytest.mark.skipif(not HAS_FASTAPI, reason="fastapi is not installed in this environment")

if HAS_FASTAPI:
    from fastapi.testclient import TestClient

    from backend.app import create_app


@pytest.fixture
def client(tmp_path):
    if not HAS_FASTAPI:
        pytest.skip("fastapi is not installed")
    app = create_app(str(tmp_path / "test.db"))
    return TestClient(app)


def test_intake_creates_session(client: "TestClient") -> None:
    response = client.post("/intake", json={"text": "Write a dark magic school story"})
    assert response.status_code == 200
    payload = response.json()
    assert "session_id" in payload
    assert isinstance(payload["session_id"], str)


def test_proposal_returns_required_keys(client: "TestClient") -> None:
    session_id = client.post("/intake", json={"text": "A hopeful detective tale"}).json()["session_id"]

    response = client.get(f"/proposal/{session_id}")
    assert response.status_code == 200
    payload = response.json()
    for key in [
        "requirement_spec",
        "expansion_suggestions",
        "outline_lite",
        "open_questions",
        "version",
        "status",
        "change_summary",
    ]:
        assert key in payload


def test_edit_increments_version_and_changes_something(client: "TestClient") -> None:
    session_id = client.post("/intake", json={"text": "Plan a short thriller"}).json()["session_id"]
    initial = client.get(f"/proposal/{session_id}").json()

    edited = client.post(
        "/decision",
        json={"session_id": session_id, "action": "edit", "text": "Also include first person perspective"},
    ).json()

    assert edited["version"] == initial["version"] + 1
    assert edited["requirement_spec"]["raw_text"] != initial["requirement_spec"]["raw_text"]


def test_approve_flips_status_to_approved(client: "TestClient") -> None:
    session_id = client.post("/intake", json={"text": "Plan a novel"}).json()["session_id"]
    client.get(f"/proposal/{session_id}")

    response = client.post("/decision", json={"session_id": session_id, "action": "approve"})
    assert response.status_code == 200
    assert response.json()["status"] == "APPROVED"
