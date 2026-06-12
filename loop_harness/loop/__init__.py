"""One-shot evidence loop orchestration.

This package coordinates a bounded Trigger -> Run -> Record -> Evaluate ->
Proposal -> Policy -> Shadow -> Compare flow. It is not an autonomous infinite
loop and must stay scoped to evidence review.
"""

from loop_harness.loop.engine import AgentLoopEngine, ProposalFactory
from loop_harness.loop.models import LoopRun, LoopStatus, LoopStep, LoopStepLog
from loop_harness.loop.store import AgentLoopStore

CLEANUP_STATUS = "evidence_support"
REPLACEMENT_PATH = "bounded evidence loop / external workflow evidence ingestion"

__all__ = [
    "AgentLoopEngine",
    "AgentLoopStore",
    "LoopRun",
    "LoopStatus",
    "LoopStep",
    "LoopStepLog",
    "ProposalFactory",
]
