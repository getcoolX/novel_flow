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


def test_plan_returns_409_when_not_approved(client: "TestClient") -> None:
    session_id = client.post("/intake", json={"text": "Plan a noir novel"}).json()["session_id"]
    response = client.get(f"/plan/{session_id}")
    assert response.status_code == 409


def test_plan_generates_once_and_reuses_persisted_payload(client: "TestClient") -> None:
    session_id = client.post("/intake", json={"text": "Plan a novel"}).json()["session_id"]
    client.get(f"/proposal/{session_id}")
    client.post("/decision", json={"session_id": session_id, "action": "approve"})

    first = client.get(f"/plan/{session_id}")
    assert first.status_code == 200
    first_payload = first.json()

    second = client.get(f"/plan/{session_id}")
    assert second.status_code == 200
    second_payload = second.json()

    assert first_payload == second_payload


def test_plan_second_call_does_not_reinvoke_generation(tmp_path, monkeypatch) -> None:
    if not HAS_FASTAPI:
        pytest.skip("fastapi is not installed")

    from backend import app as app_module

    calls = {"bible": 0, "outline": 0}

    original_bible = app_module.freeze_bible_node
    original_outline = app_module.plan_book_node

    def tracked_bible(*args, **kwargs):
        calls["bible"] += 1
        return original_bible(*args, **kwargs)

    def tracked_outline(*args, **kwargs):
        calls["outline"] += 1
        return original_outline(*args, **kwargs)

    monkeypatch.setattr(app_module, "freeze_bible_node", tracked_bible)
    monkeypatch.setattr(app_module, "plan_book_node", tracked_outline)

    local_client = TestClient(app_module.create_app(str(tmp_path / "once.db")))
    session_id = local_client.post("/intake", json={"text": "Plan a novel"}).json()["session_id"]
    local_client.get(f"/proposal/{session_id}")
    local_client.post("/decision", json={"session_id": session_id, "action": "approve"})

    assert local_client.get(f"/plan/{session_id}").status_code == 200
    assert local_client.get(f"/plan/{session_id}").status_code == 200

    assert calls == {"bible": 1, "outline": 1}
