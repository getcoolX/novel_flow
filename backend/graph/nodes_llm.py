from __future__ import annotations

from backend.graph.prompts import analyze_prompts, expand_prompts, outline_lite_prompts
from backend.graph.schemas import ExpansionResult, OutlineLite, ProposalPackage, ProposalStatus, RequirementSpec
from backend.llm.client import LLMClient


def analyze(raw_text: str, client: LLMClient) -> RequirementSpec:
    system_prompt, user_prompt = analyze_prompts(raw_text)
    data = client.generate_json(system_prompt=system_prompt, user_prompt=user_prompt, schema_name="RequirementSpec")
    return RequirementSpec.model_validate(data)


def expand(spec: RequirementSpec, client: LLMClient) -> ExpansionResult:
    system_prompt, user_prompt = expand_prompts(spec)
    data = client.generate_json(system_prompt=system_prompt, user_prompt=user_prompt, schema_name="ExpansionResult")
    return ExpansionResult.model_validate(data)


def outline_lite(spec: RequirementSpec, client: LLMClient) -> OutlineLite:
    system_prompt, user_prompt = outline_lite_prompts(spec)
    data = client.generate_json(system_prompt=system_prompt, user_prompt=user_prompt, schema_name="OutlineLite")
    return OutlineLite.model_validate(data)


def build_proposal(text: str, version: int, status: ProposalStatus, client: LLMClient) -> ProposalPackage:
    spec = analyze(text, client)
    expanded = expand(spec, client)
    outline = outline_lite(spec, client)
    return ProposalPackage(
        requirement_spec=spec,
        expansion_suggestions=expanded.expansion_suggestions,
        outline_lite=outline,
        open_questions=expanded.open_questions,
        version=version,
        status=status,
        change_summary="Generated from latest requirement input.",
    )
