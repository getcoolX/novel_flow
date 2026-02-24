import importlib.util

import pytest

from backend.storage.sqlite import SessionsRepo

HAS_PYDANTIC = importlib.util.find_spec("pydantic") is not None

if HAS_PYDANTIC:
    from backend.graph.placeholder import build_proposal
    from backend.graph.schemas import ProposalStatus


@pytest.mark.skipif(not HAS_PYDANTIC, reason="pydantic is not installed in this environment")
def test_placeholder_builds_eight_beats() -> None:
    proposal = build_proposal("A magic tale", version=1, status=ProposalStatus.NEEDS_CONFIRMATION)
    assert len(proposal.outline_lite.chapter_beats) == 8


def test_repo_create_and_get(tmp_path) -> None:
    repo = SessionsRepo(str(tmp_path / "state.db"))
    session_id = repo.create_session("Need a mystery novel")
    row = repo.get_session(session_id)
    assert row is not None
    assert row["status"] == "NEW"
    assert row["version"] == 0
