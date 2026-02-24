from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from backend.graph.graph import apply_decision as apply_decision_graph
from backend.graph.graph import run_proposal as run_proposal_graph
from backend.graph.nodes_llm import freeze_bible_node, plan_book_node
from backend.graph.schemas import PlanPackage, ProposalPackage, ProposalStatus
from backend.llm.client import LLMClient
from backend.storage.sqlite import SessionsRepo


class IntakeRequest(BaseModel):
    text: str


class IntakeResponse(BaseModel):
    session_id: str


class DecisionRequest(BaseModel):
    session_id: str
    action: str
    text: str | None = None


class RegenerateRequest(BaseModel):
    force: bool = False


def create_app(db_path: str | None = None) -> FastAPI:
    app = FastAPI(title="novel_flow backend")
    repo = SessionsRepo(db_path or os.getenv("NOVEL_FLOW_DB", "novel_flow.db"))
    llm_client = LLMClient(temperature=0)

    def get_or_generate_plan(session_id: str, *, force: bool = False) -> PlanPackage:
        session = repo.get_session(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        if session["status"] != ProposalStatus.APPROVED.value:
            raise HTTPException(status_code=409, detail="Session is not approved")

        if not force and session.get("bible_json") and session.get("outline_full_json"):
            return PlanPackage(
                bible=session["bible_json"],
                outline_full=session["outline_full_json"],
                bible_version=int(session.get("bible_version") or 1),
                outline_version=int(session.get("outline_version") or 1),
            )

        proposal_json = session.get("proposal_json")
        if proposal_json is None or session.get("spec_json") is None:
            raise HTTPException(status_code=409, detail="Approved proposal payload missing")

        proposal = ProposalPackage.model_validate(proposal_json)
        spec = proposal.requirement_spec

        bible = freeze_bible_node(spec=spec, proposal=proposal, client=llm_client)
        outline_full = plan_book_node(bible=bible, spec=spec, client=llm_client)

        bible_version = int(session.get("bible_version") or 1)
        outline_version = int(session.get("outline_version") or 1)
        if force:
            bible_version += 1
            outline_version += 1

        repo.update_session(
            session_id,
            bible_json=bible.model_dump(mode="json"),
            outline_full_json=outline_full.model_dump(mode="json"),
            bible_version=bible_version,
            outline_version=outline_version,
        )
        return PlanPackage(
            bible=bible,
            outline_full=outline_full,
            bible_version=bible_version,
            outline_version=outline_version,
        )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/intake", response_model=IntakeResponse)
    def intake(payload: IntakeRequest) -> IntakeResponse:
        return IntakeResponse(session_id=repo.create_session(payload.text))

    @app.get("/proposal/{session_id}", response_model=ProposalPackage)
    def proposal(session_id: str) -> ProposalPackage:
        session = repo.get_session(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")

        return run_proposal_graph(session_id=session_id, repo=repo, client=llm_client)

    @app.post("/decision", response_model=ProposalPackage)
    def decision(payload: DecisionRequest) -> ProposalPackage:
        session = repo.get_session(payload.session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")

        try:
            return apply_decision_graph(
                session_id=payload.session_id,
                action=payload.action,
                text=payload.text,
                repo=repo,
                client=llm_client,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @app.get("/plan/{session_id}", response_model=PlanPackage)
    def plan(session_id: str) -> PlanPackage:
        return get_or_generate_plan(session_id=session_id)

    @app.post("/plan/{session_id}/regenerate", response_model=PlanPackage)
    def regenerate_plan(session_id: str, payload: RegenerateRequest) -> PlanPackage:
        if not payload.force:
            raise HTTPException(status_code=400, detail="force must be true")
        return get_or_generate_plan(session_id=session_id, force=True)

    return app


app = create_app()
