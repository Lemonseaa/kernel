"""Isolated low-risk autonomy guardrails.

Autonomy is not a product direction by itself. It is a guarded queue for
approved, reversible evidence actions only. Live trading, publishing, or other
sensitive side effects remain outside automatic execution.
"""

from checkpoint_ai.autonomy.eligibility import AutoExecutionEligibility, EligibilityResult
from checkpoint_ai.autonomy.feedback import OperatorFeedbackAnalyzer
from checkpoint_ai.autonomy.models import AutonomyActionLog, AutonomyActionStatus
from checkpoint_ai.autonomy.queue import AutoActionQueue
from checkpoint_ai.autonomy.store import AutonomyActionStore, AutonomyQueueStateStore

CLEANUP_STATUS = "isolate"
REPLACEMENT_PATH = "human-approved evidence action queue"

__all__ = [
    "AutoActionQueue",
    "AutoExecutionEligibility",
    "AutonomyActionLog",
    "AutonomyActionStatus",
    "AutonomyActionStore",
    "AutonomyQueueStateStore",
    "EligibilityResult",
    "OperatorFeedbackAnalyzer",
]
