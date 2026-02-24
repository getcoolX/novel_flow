from __future__ import annotations

import importlib.util

import pytest

HAS_PYDANTIC = importlib.util.find_spec("pydantic") is not None
HAS_LANGGRAPH = importlib.util.find_spec("langgraph") is not None
pytestmark = pytest.mark.skipif(
    not (HAS_PYDANTIC and HAS_LANGGRAPH), reason="pydantic and langgraph are required in this environment"
)

if HAS_PYDANTIC and HAS_LANGGRAPH:
    from backend.graph.graph import ProposalGraphService
    from backend.llm.client import LLMClient
    from backend.storage.sqlite import SessionsRepo


@pytest.mark.skipif(not (HAS_PYDANTIC and HAS_LANGGRAPH), reason="pydantic and langgraph are required in this environment")
def test_edit_loops_back_and_increments_version(tmp_path) -> None:
    repo = SessionsRepo(str(tmp_path / "state.db"))
    client = LLMClient(api_key=None)
    service = ProposalGraphService(repo=repo, client=client)

    session_id = repo.create_session("Plan a short thriller")
    initial = service.run_proposal(session_id)

    edited = service.apply_decision(session_id, action="edit", text="Use first person perspective")

    assert edited.version == initial.version + 1
    assert edited.status.value == "NEEDS_CONFIRMATION"
    assert edited.requirement_spec.raw_text != initial.requirement_spec.raw_text


@pytest.mark.skipif(not (HAS_PYDANTIC and HAS_LANGGRAPH), reason="pydantic and langgraph are required in this environment")
def test_approve_reaches_terminal_status(tmp_path) -> None:
    repo = SessionsRepo(str(tmp_path / "state.db"))
    client = LLMClient(api_key=None)
    service = ProposalGraphService(repo=repo, client=client)

    session_id = repo.create_session("Plan a novel")
    service.run_proposal(session_id)

    approved = service.apply_decision(session_id, action="approve")

    assert approved.status.value == "APPROVED"
    stored = repo.get_session(session_id)
    assert stored is not None
    assert stored["status"] == "APPROVED"
