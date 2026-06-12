"""Prompt versioning and proposal contracts.

Prompt changes are evidence artifacts: patch-first, versioned, reviewable, and
rollbackable. This package stays only as a candidate-change contract layer, not
as an autonomous prompt rewriting system.
"""

from checkpoint_ai.prompt.models import (
    PromptPatch,
    PromptProposal,
    PromptProposalStatus,
    PromptSlot,
    PromptVersion,
    Proposal,
    ProposalKind,
    ProposalPatch,
    ProposalStatus,
    ProposalTargetType,
)
from checkpoint_ai.prompt.storage import PromptProposalStore, PromptVersionStore, ProposalStore

CLEANUP_STATUS = "evidence_support"
REPLACEMENT_PATH = "candidate patch evidence with version snapshots"

__all__ = [
    "Proposal",
    "ProposalKind",
    "ProposalPatch",
    "ProposalStatus",
    "ProposalStore",
    "ProposalTargetType",
    "PromptPatch",
    "PromptProposal",
    "PromptProposalStatus",
    "PromptProposalStore",
    "PromptSlot",
    "PromptVersion",
    "PromptVersionStore",
]
