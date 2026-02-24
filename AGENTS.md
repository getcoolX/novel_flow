# AGENTS.md

## Project mission
This repository implements an **interactive planning → user approval loop → fully automated novel generation** workflow.

## Durable engineering rules
- All LLM-facing outputs **must** be strict JSON.
- All LLM-facing JSON must be validated against explicit schemas before use.

## Directory conventions
Keep code organized under these paths:
- `backend/`
- `backend/graph/`
- `backend/prompts/`
- `backend/storage/`
- `backend/tests/`

## Preferred commands
- Install: `pip install -e .[dev]`
- Run: `uvicorn backend.app:app --reload`
- Test: `pytest -q`

## Pull request expectations
- PRs must include tests for any non-trivial logic changes.
