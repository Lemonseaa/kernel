"""Human approval gate."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4

from kernel.control.policy import PolicyEvaluation
from kernel.events import EventBus, EventType
from kernel.notification import NotificationManager


class ApprovalState(str, Enum):
    """Human approval states."""

    REQUESTED = "requested"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass(slots=True)
class ApprovalRequest:
    """Approval request payload."""

    policy: PolicyEvaluation
    message: str = ""
    subject: Any = None
    state: ApprovalState = ApprovalState.REQUESTED
    id: str = field(default_factory=lambda: str(uuid4()))


class HumanApprovalGate:
    """Optional human approval gate."""

    def __init__(
        self,
        auto_approve: bool | None = True,
        event_bus: EventBus | None = None,
        notification_manager: NotificationManager | None = None,
    ) -> None:
        """Create a gate with optional auto approval."""

        self.auto_approve = auto_approve
        self.event_bus = event_bus
        self.notification_manager = notification_manager
        self.requests: list[ApprovalRequest] = []

    def create_request(
        self,
        policy: PolicyEvaluation,
        message: str = "",
        subject: Any = None,
    ) -> ApprovalRequest:
        """Create a pending approval request."""

        request = ApprovalRequest(policy=policy, message=message, subject=subject)
        self.requests.append(request)
        self._emit(EventType.APPROVAL_REQUESTED, request)
        if self.notification_manager is not None and subject is not None:
            self.notification_manager.notify_approval_required(subject, reason=policy.reason or message)
        return request

    def request_approval(
        self,
        policy: PolicyEvaluation,
        message: str = "",
        subject: Any = None,
    ) -> bool:
        """Request approval and return whether execution may continue."""

        request = self.create_request(policy=policy, message=message, subject=subject)
        if self.auto_approve:
            request.state = ApprovalState.APPROVED
            self._emit(EventType.APPROVAL_APPROVED, request)
        elif self.auto_approve is False:
            request.state = ApprovalState.REJECTED
            self._emit(EventType.APPROVAL_REJECTED, request)
        return request.state == ApprovalState.APPROVED

    def approve(self, request_id: str) -> bool:
        """Approve a pending request by id."""

        request = self._find_request(request_id)
        if request is None or request.state != ApprovalState.REQUESTED:
            return False
        request.state = ApprovalState.APPROVED
        self._emit(EventType.APPROVAL_APPROVED, request)
        return True

    def reject(self, request_id: str) -> bool:
        """Reject a pending request by id."""

        request = self._find_request(request_id)
        if request is None or request.state != ApprovalState.REQUESTED:
            return False
        request.state = ApprovalState.REJECTED
        self._emit(EventType.APPROVAL_REJECTED, request)
        return True

    def wait_for_approval(self, request_id: str) -> bool:
        """Return the current approval result for a request."""

        request = self._find_request(request_id)
        return request is not None and request.state == ApprovalState.APPROVED

    def pending_requests(self) -> list[ApprovalRequest]:
        """Return unresolved approval requests."""

        return [request for request in self.requests if request.state == ApprovalState.REQUESTED]

    def _find_request(self, request_id: str) -> ApprovalRequest | None:
        """Find a request by id."""

        for request in self.requests:
            if request.id == request_id:
                return request
        return None

    def _emit(self, event_type: EventType, request: ApprovalRequest) -> None:
        """Emit approval event when an event bus is configured."""

        if self.event_bus is None:
            return
        subject = request.subject
        payload = {
            "approval_id": request.id,
            "policy_id": request.policy.id,
            "state": request.state.value,
            "message": request.message,
        }
        if hasattr(subject, "id"):
            payload["subject_id"] = subject.id
        self.event_bus.emit(event_type, payload)
