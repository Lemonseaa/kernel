"""Isolated low-risk autonomy guardrails.

Autonomy is not a product direction by itself. It is a guarded queue for
approved, reversible evidence actions only. Live trading, publishing, or other
sensitive side effects remain outside automatic execution.
"""

from loop_harness.autonomy.eligibility import AutoExecutionEligibility, EligibilityResult
from loop_harness.autonomy.feedback import OperatorFeedbackAnalyzer
from loop_harness.autonomy.models import AutonomyActionLog, AutonomyActionStatus
from loop_harness.autonomy.queue import AutoActionQueue
from loop_harness.autonomy.store import AutonomyActionStore, AutonomyQueueStateStore

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
