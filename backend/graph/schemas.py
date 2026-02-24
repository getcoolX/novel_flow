from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class ProposalStatus(str, Enum):
    NEW = "NEW"
    NEEDS_CONFIRMATION = "NEEDS_CONFIRMATION"
    APPROVED = "APPROVED"


class RequirementSpec(StrictModel):
    raw_text: str
    objective: str
    genre_hint: str
    tone_hint: str
    constraints: list[str] = Field(default_factory=list)


class ExpansionResult(StrictModel):
    expansion_suggestions: list[str]
    open_questions: list[str]


class OutlineLite(StrictModel):
    chapter_beats: list[str] = Field(min_length=8, max_length=8)


class ProposalPackage(StrictModel):
    requirement_spec: RequirementSpec
    expansion_suggestions: list[str]
    outline_lite: OutlineLite
    open_questions: list[str]
    version: int
    status: ProposalStatus
    change_summary: str = ""
