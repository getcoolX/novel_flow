from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ProposalStatus(str, Enum):
    NEW = "NEW"
    NEEDS_CONFIRMATION = "NEEDS_CONFIRMATION"
    APPROVED = "APPROVED"


class RequirementSpec(BaseModel):
    raw_text: str
    objective: str
    genre_hint: str
    tone_hint: str
    constraints: list[str] = Field(default_factory=list)


class OutlineLite(BaseModel):
    chapter_beats: list[str] = Field(min_length=8, max_length=8)


class ProposalPackage(BaseModel):
    requirement_spec: RequirementSpec
    expansion_suggestions: list[str]
    outline_lite: OutlineLite
    open_questions: list[str]
    version: int
    status: ProposalStatus
