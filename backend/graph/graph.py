from __future__ import annotations

from langgraph.graph import END, StateGraph

from backend.graph.nodes_llm import analyze, expand, outline_lite
from backend.graph.schemas import ProposalPackage, ProposalStatus
from backend.graph.state import SessionState
from backend.llm.client import LLMClient
from backend.storage.sqlite import SessionsRepo


class ProposalGraphService:
    def __init__(self, repo: SessionsRepo, client: LLMClient) -> None:
        self.repo = repo
        self.client = client
        self.graph = self._build_graph()

    def _build_graph(self) -> object:
        builder = StateGraph(SessionState)
        builder.add_node("INTAKE", self._intake)
        builder.add_node("ANALYZE", self._analyze)
        builder.add_node("EXPAND", self._expand)
        builder.add_node("OUTLINE_LITE", self._outline_lite)
        builder.add_node("PRESENT", self._present)
        builder.add_node("WAIT_DECISION", self._wait_decision)
        builder.add_node("APPROVED", self._approved)

        builder.set_entry_point("INTAKE")
        builder.add_edge("INTAKE", "ANALYZE")
        builder.add_edge("ANALYZE", "EXPAND")
        builder.add_edge("EXPAND", "OUTLINE_LITE")
        builder.add_edge("OUTLINE_LITE", "PRESENT")
        builder.add_edge("PRESENT", "WAIT_DECISION")
        builder.add_conditional_edges(
            "WAIT_DECISION",
            self._route_wait_decision,
            {
                "edit": "ANALYZE",
                "approve": "APPROVED",
                "reset": "INTAKE",
                "end": END,
            },
        )
        builder.add_edge("APPROVED", END)
        return builder.compile()

    def _load_state(self, session_id: str) -> SessionState:
        session = self.repo.get_session(session_id)
        if session is None:
            raise ValueError("Session not found")

        proposal = None
        if session["proposal_json"] is not None:
            proposal = ProposalPackage.model_validate(session["proposal_json"])

        return SessionState(
            session_id=session_id,
            raw_text=session["requirement_text"],
            spec=session["spec_json"],
            proposal=proposal,
            status=session["status"],
            version=int(session["version"]),
            last_user_action=session.get("last_user_action"),
            edit_text=session.get("edit_text"),
        )

    def _persist_state(self, state: SessionState) -> None:
        self.repo.update_session(
            state.session_id,
            requirement_text=state.raw_text,
            spec_json=state.spec.model_dump(mode="json") if state.spec else None,
            proposal_json=state.proposal.model_dump(mode="json") if state.proposal else None,
            status=state.status,
            version=state.version,
            last_user_action=state.last_user_action,
            edit_text=state.edit_text,
        )

    def _intake(self, state: SessionState) -> SessionState:
        if state.last_user_action == "reset":
            state.spec = None
            state.proposal = None
            state.status = ProposalStatus.NEW.value
            state.version = 0
            state.last_user_action = None
            state.edit_text = None
        return state

    def _analyze(self, state: SessionState) -> SessionState:
        if state.last_user_action == "edit":
            patch_text = (state.edit_text or "").strip()
            state.raw_text = (state.raw_text + "\n" + patch_text).strip()
            state.version += 1
            state.last_user_action = None
            state.edit_text = None

        state.spec = analyze(state.raw_text, client=self.client)
        return state

    def _expand(self, state: SessionState) -> SessionState:
        if state.spec is None:
            raise ValueError("Requirement spec missing before EXPAND")
        expanded = expand(state.spec, client=self.client)
        state.expansion_suggestions = expanded.expansion_suggestions
        state.open_questions = expanded.open_questions
        return state

    def _outline_lite(self, state: SessionState) -> SessionState:
        if state.spec is None:
            raise ValueError("Requirement spec missing before OUTLINE_LITE")
        outline = outline_lite(state.spec, client=self.client)
        state.proposal = ProposalPackage(
            requirement_spec=state.spec,
            expansion_suggestions=state.expansion_suggestions,
            outline_lite=outline,
            open_questions=state.open_questions,
            version=max(1, state.version),
            status=ProposalStatus.NEEDS_CONFIRMATION,
            change_summary="Generated from latest requirement input.",
        )
        state.status = ProposalStatus.NEEDS_CONFIRMATION.value
        state.version = state.proposal.version
        return state

    def _present(self, state: SessionState) -> SessionState:
        if state.proposal is None:
            raise ValueError("Proposal missing before PRESENT")
        self._persist_state(state)
        return state

    def _wait_decision(self, state: SessionState) -> SessionState:
        return state

    def _approved(self, state: SessionState) -> SessionState:
        if state.proposal is None:
            state.spec = analyze(state.raw_text, client=self.client)
            expanded = expand(state.spec, client=self.client)
            outline = outline_lite(state.spec, client=self.client)
            state.proposal = ProposalPackage(
                requirement_spec=state.spec,
                expansion_suggestions=expanded.expansion_suggestions,
                outline_lite=outline,
                open_questions=expanded.open_questions,
                version=max(1, state.version),
                status=ProposalStatus.APPROVED,
                change_summary="Generated from latest requirement input.",
            )
        else:
            state.proposal.status = ProposalStatus.APPROVED
        state.status = ProposalStatus.APPROVED.value
        self._persist_state(state)
        return state

    @staticmethod
    def _route_wait_decision(state: SessionState) -> str:
        action = (state.last_user_action or "").lower()
        if action in {"edit", "approve", "reset"}:
            return action
        return "end"

    def run_proposal(self, session_id: str) -> ProposalPackage:
        start = self._load_state(session_id)
        start.last_user_action = None
        end_state = SessionState.model_validate(self.graph.invoke(start))
        if end_state.proposal is None:
            raise ValueError("Proposal generation did not produce output")
        return end_state.proposal

    def apply_decision(self, session_id: str, action: str, text: str | None = None) -> ProposalPackage:
        action_normalized = action.lower()
        if action_normalized not in {"edit", "approve", "reset"}:
            raise ValueError("Unsupported action")

        state = self._load_state(session_id)
        state.last_user_action = action_normalized
        state.edit_text = text

        end_state = SessionState.model_validate(self.graph.invoke(state))

        if end_state.proposal is None:
            raise ValueError("Decision did not produce output")
        return end_state.proposal


def run_proposal(session_id: str, repo: SessionsRepo, client: LLMClient) -> ProposalPackage:
    return ProposalGraphService(repo=repo, client=client).run_proposal(session_id)


def apply_decision(
    session_id: str,
    action: str,
    text: str | None,
    repo: SessionsRepo,
    client: LLMClient,
) -> ProposalPackage:
    return ProposalGraphService(repo=repo, client=client).apply_decision(session_id=session_id, action=action, text=text)
