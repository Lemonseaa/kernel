"""One-shot evidence loop orchestration.

This package coordinates a bounded Trigger -> Run -> Record -> Evaluate ->
Proposal -> Policy -> Shadow -> Compare flow. It is not an autonomous infinite
loop and must stay scoped to evidence review.
"""

from checkpoint_ai.loop.engine import AgentLoopEngine, ProposalFactory
from checkpoint_ai.loop.models import LoopRun, LoopStatus, LoopStep, LoopStepLog
from checkpoint_ai.loop.store import AgentLoopStore

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
