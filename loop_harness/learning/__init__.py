"""Transitional evidence-review learning loop exports.

This package must not become an autonomous self-improvement engine. Keep it
focused on evidence-backed observations, small candidate proposals, shadow
validation, and safety findings.
"""

from loop_harness.learning.aggregation import ObservationAggregator
from loop_harness.learning.loop import LearningLoopService
from loop_harness.learning.models import (
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
from loop_harness.learning.observers import DecisionObserver, MetricObserver
from loop_harness.learning.proposers import ParameterProposer, PromptProposer
from loop_harness.learning.ranking import ConflictDetector, ProposalRanker
from loop_harness.learning.safety import SafetyMonitor
from loop_harness.learning.scheduler import ShadowReplayScheduler
from loop_harness.learning.store import (
    ObservationStore,
    SafetyFindingStore,
    ValidationSummaryStore,
)
from loop_harness.learning.validator import Validator

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
