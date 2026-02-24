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


class StyleGuide(StrictModel):
    diction: str
    sentence_length: str
    dialogue_ratio: str
    taboo_list: list[str] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)


class WorldInfo(StrictModel):
    setting_time: str
    setting_place: str
    rules: list[str] = Field(default_factory=list)
    factions: list[str] = Field(default_factory=list)
    tech_or_magic_level: str


class CharacterEntry(StrictModel):
    name: str
    role: str
    goal: str
    flaw: str
    secret: str
    voice: str
    relationships: list[str] = Field(default_factory=list)


class TimelineEntry(StrictModel):
    id: str
    event: str
    when: str
    consequences: str


class StoryBible(StrictModel):
    title_working: str
    genre: str
    tone: str
    pov: str
    style_guide: StyleGuide
    world: WorldInfo
    characters: list[CharacterEntry] = Field(default_factory=list)
    timeline: list[TimelineEntry] = Field(default_factory=list)
    canon_rules: list[str] = Field(default_factory=list)


class OutlineChapter(StrictModel):
    index: int
    title: str
    goal: str
    conflict: str
    twist: str
    hook: str
    locations: list[str] = Field(default_factory=list)
    characters_involved: list[str] = Field(default_factory=list)
    foreshadowing_in: list[str] = Field(default_factory=list)
    foreshadowing_out: list[str] = Field(default_factory=list)


class CharacterArc(StrictModel):
    character: str
    start_state: str
    key_turns: list[str] = Field(default_factory=list)
    end_state: str


class ForeshadowingRow(StrictModel):
    id: str
    setup_chapter: int
    payoff_chapter: int
    description: str
    evidence_style: str


class EndingPlan(StrictModel):
    type: str
    final_reveal: str
    emotional_resolution: str


class OutlineFull(StrictModel):
    chapters: list[OutlineChapter] = Field(default_factory=list)
    character_arcs: list[CharacterArc] = Field(default_factory=list)
    foreshadowing_table: list[ForeshadowingRow] = Field(default_factory=list)
    ending: EndingPlan


class PlanPackage(StrictModel):
    bible: StoryBible
    outline_full: OutlineFull
    bible_version: int
    outline_version: int
