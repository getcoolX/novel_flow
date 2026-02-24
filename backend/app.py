from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from backend.graph.placeholder import build_proposal
from backend.graph.schemas import ProposalPackage, ProposalStatus
from backend.storage.sqlite import SessionsRepo


class IntakeRequest(BaseModel):
    text: str


class IntakeResponse(BaseModel):
    session_id: str


class DecisionRequest(BaseModel):
    session_id: str
    action: str
    text: str | None = None


def create_app(db_path: str | None = None) -> FastAPI:
    app = FastAPI(title="novel_flow backend")
    repo = SessionsRepo(db_path or os.getenv("NOVEL_FLOW_DB", "novel_flow.db"))

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

        if session["proposal_json"] is None:
            version = max(1, int(session["version"]))
            pkg = build_proposal(session["requirement_text"], version=version, status=ProposalStatus.NEEDS_CONFIRMATION)
            repo.update_session(
                session_id,
                spec_json=pkg.requirement_spec.model_dump(),
                proposal_json=pkg.model_dump(mode="json"),
                status=pkg.status.value,
                version=pkg.version,
            )
            return pkg

        return ProposalPackage.model_validate(session["proposal_json"])

    @app.post("/decision", response_model=ProposalPackage)
    def decision(payload: DecisionRequest) -> ProposalPackage:
        session = repo.get_session(payload.session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")

        action = payload.action.lower()
        if action == "approve":
            current = session["proposal_json"]
            if current is None:
                version = max(1, int(session["version"]))
                pkg = build_proposal(session["requirement_text"], version=version, status=ProposalStatus.APPROVED)
            else:
                pkg = ProposalPackage.model_validate(current)
                pkg.status = ProposalStatus.APPROVED
            repo.update_session(
                payload.session_id,
                proposal_json=pkg.model_dump(mode="json"),
                spec_json=pkg.requirement_spec.model_dump(),
                status=pkg.status.value,
                version=pkg.version,
            )
            return pkg

        if action == "edit":
            patch_text = payload.text or ""
            updated_requirement = (session["requirement_text"] + "\n" + patch_text).strip()
            version = int(session["version"]) + 1
            pkg = build_proposal(updated_requirement, version=version, status=ProposalStatus.NEEDS_CONFIRMATION)
            repo.update_session(
                payload.session_id,
                requirement_text=updated_requirement,
                spec_json=pkg.requirement_spec.model_dump(),
                proposal_json=pkg.model_dump(mode="json"),
                status=pkg.status.value,
                version=pkg.version,
            )
            return pkg

        if action == "reset":
            repo.update_session(
                payload.session_id,
                spec_json=None,
                proposal_json=None,
                status=ProposalStatus.NEW.value,
                version=0,
            )
            pkg = build_proposal(session["requirement_text"], version=0, status=ProposalStatus.NEW)
            return pkg

        raise HTTPException(status_code=400, detail="Unsupported action")

    return app


app = create_app()
