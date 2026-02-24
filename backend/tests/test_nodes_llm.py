from __future__ import annotations

import importlib.util

import pytest

HAS_PYDANTIC = importlib.util.find_spec("pydantic") is not None
pytestmark = pytest.mark.skipif(not HAS_PYDANTIC, reason="pydantic is not installed in this environment")

if HAS_PYDANTIC:
    from pydantic import ValidationError

    from backend.graph.nodes_llm import analyze
    from backend.graph.schemas import OutlineFull, StoryBible
    from backend.llm.client import LLMClient

    class SequencedClient(LLMClient):
        def __init__(self, responses: list[str]) -> None:
            super().__init__(api_key="test-key")
            self.responses = responses
            self.calls = 0

        def _call_model(self, *, system_prompt: str, user_prompt: str) -> str:
            response = self.responses[self.calls]
            self.calls += 1
            return response


@pytest.mark.skipif(not HAS_PYDANTIC, reason="pydantic is not installed")
def test_generate_json_retries_invalid_then_valid() -> None:
    client = SequencedClient(
        responses=[
            "not-json",
            (
                '{"raw_text":"Need a cozy mystery",'
                '"objective":"Plan a cozy mystery novel",'
                '"genre_hint":"mystery",'
                '"tone_hint":"warm",'
                '"constraints":["single POV"]}'
            ),
        ]
    )

    spec = analyze("Need a cozy mystery", client=client)

    assert client.calls == 2
    assert spec.genre_hint == "mystery"


@pytest.mark.skipif(not HAS_PYDANTIC, reason="pydantic is not installed")
def test_story_bible_schema_forbids_extra_keys() -> None:
    with pytest.raises(ValidationError):
        StoryBible.model_validate(
            {
                "title_working": "x",
                "genre": "fantasy",
                "tone": "dark",
                "pov": "first person",
                "style_guide": {
                    "diction": "tight",
                    "sentence_length": "short",
                    "dialogue_ratio": "30%",
                    "taboo_list": [],
                    "unexpected": "boom",
                },
                "world": {
                    "setting_time": "now",
                    "setting_place": "city",
                    "rules": [],
                    "factions": [],
                    "tech_or_magic_level": "low",
                },
                "characters": [],
                "timeline": [],
                "canon_rules": [],
            }
        )


@pytest.mark.skipif(not HAS_PYDANTIC, reason="pydantic is not installed")
def test_outline_full_schema_forbids_extra_keys() -> None:
    with pytest.raises(ValidationError):
        OutlineFull.model_validate(
            {
                "chapters": [],
                "character_arcs": [],
                "foreshadowing_table": [],
                "ending": {
                    "type": "closed",
                    "final_reveal": "none",
                    "emotional_resolution": "calm",
                    "extra": "not allowed",
                },
            }
        )
