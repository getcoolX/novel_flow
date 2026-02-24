from __future__ import annotations

import importlib.util

import pytest

HAS_PYDANTIC = importlib.util.find_spec("pydantic") is not None
pytestmark = pytest.mark.skipif(not HAS_PYDANTIC, reason="pydantic is not installed in this environment")

if HAS_PYDANTIC:
    from backend.graph.nodes_llm import analyze
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


@pytest.mark.skipif(not HAS_PYDANTIC, reason="pydantic is not installed in this environment")
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
