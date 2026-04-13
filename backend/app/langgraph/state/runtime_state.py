"""
RuntimeState
- session: SessionGraphState
- round: RoundGraphState
- interviewer: InterviewerExecutionState
- evaluation: EvaluationState

Not needed for now, but will be needed for later.
"""

from __future__ import annotations

from .session_state import SessionGraphState
from .round_state import RoundGraphState
from .interviewer_state import InterviewerExecutionState
from .evaluation_state import EvaluationState
from .shared_types import StateModel

class RuntimeState(StateModel):
    session: SessionGraphState
    round: RoundGraphState
    interviewer: InterviewerExecutionState
    evaluation: EvaluationState