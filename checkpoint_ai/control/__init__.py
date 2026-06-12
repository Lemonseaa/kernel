"""Isolated runtime control exports.

The runtime policy and human gate remain for compatibility with the legacy
workflow engine and local safety checks. New behavior-change decisions should
flow through scenario policy, evidence reports, and the approval console.
"""

from checkpoint_ai.control.gate import ApprovalRequest, ApprovalState, HumanApprovalGate
from checkpoint_ai.control.policy import (
    PolicyDecision,
    PolicyEngine,
    PolicyEvaluation,
    PolicyRule,
    PolicyScope,
)

CLEANUP_STATUS = "isolate"
REPLACEMENT_PATH = "scenario policy / evidence review / approval console"

__all__ = [
    "ApprovalRequest",
    "ApprovalState",
    "HumanApprovalGate",
    "PolicyDecision",
    "PolicyEngine",
    "PolicyEvaluation",
    "PolicyRule",
    "PolicyScope",
]
