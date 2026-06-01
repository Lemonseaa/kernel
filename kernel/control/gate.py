"""Human approval gate."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4

from kernel.control.policy import PolicyEvaluation


class ApprovalState(str, Enum):
    """Human approval states."""

    REQUESTED = "requested"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass(slots=True)
class ApprovalRequest:
    """Approval request payload."""

    policy: PolicyEvaluation
    state: ApprovalState = ApprovalState.REQUESTED
    id: str = field(default_factory=lambda: str(uuid4()))


class HumanApprovalGate:
    """Optional human approval gate."""

    def __init__(self, auto_approve: bool = True) -> None:
        """Create a gate with optional auto approval."""

        self.auto_approve = auto_approve
        self.requests: list[ApprovalRequest] = []

    def request_approval(self, policy: PolicyEvaluation) -> bool:
        """Request approval and return whether execution may continue."""

        request = ApprovalRequest(policy=policy)
        if self.auto_approve:
            request.state = ApprovalState.APPROVED
        else:
            request.state = ApprovalState.REJECTED
        self.requests.append(request)
        return request.state == ApprovalState.APPROVED
