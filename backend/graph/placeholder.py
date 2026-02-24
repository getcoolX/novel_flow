from __future__ import annotations

from backend.graph.schemas import OutlineLite, ProposalPackage, ProposalStatus, RequirementSpec


def _tokens(text: str) -> list[str]:
    return [token.strip(".,!?;:\"'()[]{}") for token in text.split() if token.strip()]


def analyze_requirement(text: str) -> RequirementSpec:
    tokens = _tokens(text)
    top = " ".join(tokens[:10]) if tokens else "Untitled project"

    lowered = text.lower()
    genre_hint = "fantasy" if "magic" in lowered else "mystery" if "murder" in lowered else "general fiction"
    tone_hint = "dark" if "dark" in lowered else "hopeful" if "hope" in lowered else "balanced"

    constraints = []
    if "first person" in lowered:
        constraints.append("Narrative voice: first person")
    if "short" in lowered:
        constraints.append("Keep chapter beats concise")

    return RequirementSpec(
        raw_text=text,
        objective=f"Develop a novel plan for: {top}",
        genre_hint=genre_hint,
        tone_hint=tone_hint,
        constraints=constraints,
    )


def expansion_suggestions(spec: RequirementSpec) -> list[str]:
    return [
        f"Clarify protagonist arc for a {spec.genre_hint} story.",
        "Define the primary conflict escalation points.",
        f"Lock a consistent {spec.tone_hint} voice for narration.",
    ]


def outline_lite(spec: RequirementSpec) -> OutlineLite:
    return OutlineLite(
        chapter_beats=[
            f"Chapter 1: Introduce premise grounded in '{spec.genre_hint}'.",
            "Chapter 2: Catalyst disrupts the protagonist's routine.",
            "Chapter 3: First commitment to the central conflict.",
            "Chapter 4: Rising stakes with external and internal pressure.",
            "Chapter 5: Midpoint reversal reframes the objective.",
            "Chapter 6: Complications narrow available options.",
            "Chapter 7: Climax confrontation and decisive choice.",
            "Chapter 8: Resolution, fallout, and thematic closure.",
        ]
    )


def open_questions(spec: RequirementSpec) -> list[str]:
    return [
        "Who is the ideal target readership persona?",
        "What thematic message should remain after the ending?",
        f"Are there non-negotiable constraints beyond: {', '.join(spec.constraints) if spec.constraints else 'none'}?",
    ]


def build_proposal(text: str, version: int, status: ProposalStatus) -> ProposalPackage:
    spec = analyze_requirement(text)
    return ProposalPackage(
        requirement_spec=spec,
        expansion_suggestions=expansion_suggestions(spec),
        outline_lite=outline_lite(spec),
        open_questions=open_questions(spec),
        version=version,
        status=status,
    )
