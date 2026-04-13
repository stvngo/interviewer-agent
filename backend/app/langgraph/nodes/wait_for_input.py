"""
Interrupt/wait boundary for live user input.

Uses LangGraph's interrupt() to pause graph execution and wait for external
input (transcript events, code events, etc.). Requires a checkpointer to be
configured on the compiled graph.

When resumed via Command(resume=payload), the payload becomes the return
value of interrupt() and is processed into runtime state.
"""

from __future__ import annotations

from langgraph.types import interrupt

from app.langgraph.runtime.node_contracts import NodeExecutionContext, NodeResult
from app.langgraph.state import RuntimeState


def wait_for_input(
    state: RuntimeState,
    *,
    ctx: NodeExecutionContext | None = None,
) -> NodeResult:
    """
    Pause graph execution and wait for user input.

    The interrupt payload surfaces session/round context so the caller
    (API layer / WebSocket handler) knows what the graph is waiting on.

    On resume, Command(resume={"text": "...", "speaker": "user", ...})
    provides the user input which is merged into the transcript window.
    """
    _ = ctx

    user_input = interrupt({
        "type": "awaiting_user_input",
        "session_id": str(state.session.session_id),
        "round_id": str(state.round.round_id),
        "round_status": state.round.round_status,
        "question_id": str(state.round.question_id) if state.round.question_id else None,
    })

    new_state = state.model_copy(deep=True)

    if isinstance(user_input, dict):
        tw = new_state.round.transcript_window
        if "text" in user_input:
            tw.rolling_text = (tw.rolling_text + " " + user_input["text"]).strip()
            tw.user_current_state = "speaking"
        if "silence_ms" in user_input:
            tw.silence_ms = user_input["silence_ms"]
        if "user_current_state" in user_input:
            tw.user_current_state = user_input["user_current_state"]

    return NodeResult(state=new_state)
