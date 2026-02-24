from __future__ import annotations

from backend.graph.schemas import RequirementSpec

BASE_SYSTEM_PROMPT = (
    "You are a novel planning assistant. "
    "Return JSON only. No markdown, no code fences, no explanation text."
)


def analyze_prompts(raw_text: str) -> tuple[str, str]:
    user_prompt = (
        "Analyze the requirement and produce a requirement specification JSON object. "
        "Set raw_text exactly to the input text.\n"
        f"Input text:\n{raw_text}"
    )
    return BASE_SYSTEM_PROMPT, user_prompt


def expand_prompts(spec: RequirementSpec) -> tuple[str, str]:
    user_prompt = (
        "Given this requirement specification, produce JSON with expansion_suggestions and open_questions.\n"
        f"Spec:\n{spec.model_dump_json(indent=2)}"
    )
    return BASE_SYSTEM_PROMPT, user_prompt


def outline_lite_prompts(spec: RequirementSpec) -> tuple[str, str]:
    user_prompt = (
        "Given this requirement specification, produce JSON with exactly 8 chapter_beats strings.\n"
        f"Spec:\n{spec.model_dump_json(indent=2)}"
    )
    return BASE_SYSTEM_PROMPT, user_prompt
