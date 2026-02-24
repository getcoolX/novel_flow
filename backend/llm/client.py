from __future__ import annotations

import json
import os
from typing import Any
from urllib import error, request

from pydantic import ValidationError

from backend.graph.schemas import ExpansionResult, OutlineFull, OutlineLite, RequirementSpec, StoryBible


class LLMClient:
    def __init__(
        self,
        *,
        api_key: str | None = None,
        model_name: str = "gpt-4o-mini",
        timeout_s: int = 30,
        max_retries: int = 3,
        temperature: float = 0,
    ) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("OPENAI_API_KEY")
        self.model_name = model_name
        self.timeout_s = timeout_s
        self.max_retries = max_retries
        self.temperature = temperature

    def generate_json(self, *, system_prompt: str, user_prompt: str, schema_name: str) -> dict[str, Any]:
        if not self.api_key:
            return self._mock_json(schema_name=schema_name, user_prompt=user_prompt)

        prompt = user_prompt
        last_error = "unknown error"
        for _ in range(self.max_retries):
            raw = self._call_model(system_prompt=system_prompt, user_prompt=prompt)
            try:
                data = json.loads(raw)
                return self._validate_schema(schema_name=schema_name, data=data)
            except (json.JSONDecodeError, ValidationError, ValueError) as exc:
                last_error = str(exc)
                prompt = (
                    "Your previous output was invalid. Return JSON only and repair it to fit the required schema.\n"
                    f"Schema name: {schema_name}\n"
                    f"Error: {last_error}\n"
                    f"Previous output:\n{raw}"
                )

        raise ValueError(f"Failed to generate valid JSON for {schema_name} after {self.max_retries} attempts: {last_error}")

    def _validate_schema(self, schema_name: str, data: dict[str, Any]) -> dict[str, Any]:
        validators = {
            "RequirementSpec": RequirementSpec,
            "ExpansionResult": ExpansionResult,
            "OutlineLite": OutlineLite,
            "StoryBible": StoryBible,
            "OutlineFull": OutlineFull,
        }
        model = validators.get(schema_name)
        if model is None:
            raise ValueError(f"Unsupported schema_name: {schema_name}")
        return model.model_validate(data).model_dump(mode="json")

    def _call_model(self, *, system_prompt: str, user_prompt: str) -> str:
        body = {
            "model": self.model_name,
            "response_format": {"type": "json_object"},
            "temperature": self.temperature,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        req = request.Request(
            url="https://api.openai.com/v1/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=self.timeout_s) as resp:
                payload: dict[str, Any] = json.loads(resp.read().decode("utf-8"))
        except error.HTTPError as exc:
            raise RuntimeError(f"LLM request failed with status {exc.code}") from exc
        except error.URLError as exc:
            raise RuntimeError("LLM request failed due to network error") from exc

        choices = payload.get("choices") or []
        if not choices:
            raise RuntimeError("LLM response did not include choices")
        message = choices[0].get("message") or {}
        content = message.get("content")
        if not isinstance(content, str):
            raise RuntimeError("LLM response content was not a string")
        return content

    def _mock_json(self, *, schema_name: str, user_prompt: str) -> dict[str, Any]:
        text = user_prompt.split("Input text:\n")[-1].strip()
        if schema_name == "RequirementSpec":
            lowered = text.lower()
            genre = "fantasy" if "magic" in lowered else "mystery" if "detective" in lowered else "general fiction"
            tone = "dark" if "dark" in lowered else "hopeful" if "hope" in lowered else "balanced"
            return {
                "raw_text": text,
                "objective": f"Develop a novel plan for: {text[:80] or 'Untitled project'}",
                "genre_hint": genre,
                "tone_hint": tone,
                "constraints": ["Narrative voice: first person"] if "first person" in lowered else [],
            }
        if schema_name == "ExpansionResult":
            return {
                "expansion_suggestions": [
                    "Clarify protagonist arc.",
                    "Define conflict escalation points.",
                    "Set narrative voice consistency.",
                ],
                "open_questions": [
                    "Who is the target readership?",
                    "Standalone or series potential?",
                    "Any hard constraints on setting or POV?",
                ],
            }
        if schema_name == "OutlineLite":
            return {
                "chapter_beats": [
                    "Chapter 1: Introduce premise and protagonist.",
                    "Chapter 2: Inciting incident disrupts normal life.",
                    "Chapter 3: First commitment to core conflict.",
                    "Chapter 4: Rising stakes and complications.",
                    "Chapter 5: Midpoint reversal changes the plan.",
                    "Chapter 6: Crisis narrows available options.",
                    "Chapter 7: Climax and decisive confrontation.",
                    "Chapter 8: Resolution and thematic closure.",
                ]
            }
        if schema_name == "StoryBible":
            return {
                "title_working": "The Glass Ember",
                "genre": "fantasy mystery",
                "tone": "brooding but hopeful",
                "pov": "first person",
                "style_guide": {
                    "diction": "contemporary with lyrical spikes",
                    "sentence_length": "mostly medium, short in action",
                    "dialogue_ratio": "40%",
                    "taboo_list": ["anachronistic slang", "omniscient narration"],
                    "examples": ["sensory detail anchored in emotion"],
                },
                "world": {
                    "setting_time": "late industrial era",
                    "setting_place": "river-city of Vael",
                    "rules": ["binding magic requires true names"],
                    "factions": ["Guild of Lamps", "Harbor Wardens"],
                    "tech_or_magic_level": "mixed steampunk + ritual magic",
                },
                "characters": [
                    {
                        "name": "Iris Vale",
                        "role": "protagonist investigator",
                        "goal": "clear her brother's name",
                        "flaw": "impulsive risk-taking",
                        "secret": "she can hear bound names",
                        "voice": "wry and observant",
                        "relationships": ["protective of Tomas", "rivalry with Captain Roan"],
                    }
                ],
                "timeline": [
                    {"id": "T1", "event": "artifact theft", "when": "Day 0", "consequences": "city lockdown"}
                ],
                "canon_rules": ["No resurrection magic", "Magic leaves physical residue"],
            }
        if schema_name == "OutlineFull":
            return {
                "chapters": [
                    {
                        "index": 1,
                        "title": "Ash on the River",
                        "goal": "establish mystery",
                        "conflict": "Iris is framed",
                        "twist": "evidence points to Tomas",
                        "hook": "Iris pockets forbidden residue",
                        "locations": ["Dock Nine"],
                        "characters_involved": ["Iris Vale", "Captain Roan"],
                        "foreshadowing_in": ["F1"],
                        "foreshadowing_out": [],
                    }
                ],
                "character_arcs": [
                    {
                        "character": "Iris Vale",
                        "start_state": "reactive and isolated",
                        "key_turns": ["accepts help", "reveals secret"],
                        "end_state": "trusted leader",
                    }
                ],
                "foreshadowing_table": [
                    {
                        "id": "F1",
                        "setup_chapter": 1,
                        "payoff_chapter": 8,
                        "description": "residue pattern matches a ward key",
                        "evidence_style": "forensic breadcrumb",
                    }
                ],
                "ending": {
                    "type": "bittersweet victory",
                    "final_reveal": "Guild master orchestrated theft",
                    "emotional_resolution": "Iris reconciles with Tomas",
                },
            }
        raise ValueError(f"Unsupported schema_name: {schema_name}")
