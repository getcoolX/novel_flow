from __future__ import annotations

from pydantic import BaseModel, Field

from backend.graph.schemas import ProposalPackage, RequirementSpec


class SessionState(BaseModel):
    session_id: str
    raw_text: str
    spec: RequirementSpec | None = None
    proposal: ProposalPackage | None = None
    status: str = "NEW"
    version: int = 0
    last_user_action: str | None = None
    edit_text: str | None = None
    expansion_suggestions: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)
