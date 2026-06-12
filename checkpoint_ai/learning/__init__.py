"""Transitional evidence-review learning loop exports.

This package must not become an autonomous self-improvement engine. Keep it
focused on evidence-backed observations, small candidate proposals, shadow
validation, and safety findings.
"""

from checkpoint_ai.learning.aggregation import ObservationAggregator
from checkpoint_ai.learning.loop import LearningLoopService
from checkpoint_ai.learning.models import (
    LearningLoopRunResult,
    Observation,
    ObservationSeverity,
    ObservationType,
    ProposalCandidate,
    SafetyFinding,
    ShadowReplayJob,
    ShadowReplayStatus,
    ValidationSummary,
)
from checkpoint_ai.learning.observers import DecisionObserver, MetricObserver
from checkpoint_ai.learning.proposers import ParameterProposer, PromptProposer
from checkpoint_ai.learning.ranking import ConflictDetector, ProposalRanker
from checkpoint_ai.learning.safety import SafetyMonitor
from checkpoint_ai.learning.scheduler import ShadowReplayScheduler
from checkpoint_ai.learning.store import (
    ObservationStore,
    SafetyFindingStore,
    ValidationSummaryStore,
)
from checkpoint_ai.learning.validator import Validator

CLEANUP_STATUS = "rewrite"
REPLACEMENT_PATH = "ARIS-style evidence review / audit loop"

__all__ = [
    "ConflictDetector",
    "DecisionObserver",
    "LearningLoopRunResult",
    "LearningLoopService",
    "MetricObserver",
    "Observation",
    "ObservationAggregator",
    "ObservationSeverity",
    "ObservationStore",
    "ObservationType",
    "ParameterProposer",
    "PromptProposer",
    "ProposalCandidate",
    "ProposalRanker",
    "SafetyFinding",
    "SafetyFindingStore",
    "SafetyMonitor",
    "ShadowReplayJob",
    "ShadowReplayScheduler",
    "ShadowReplayStatus",
    "ValidationSummary",
    "ValidationSummaryStore",
    "Validator",
]
