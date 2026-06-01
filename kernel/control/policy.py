"""Policy engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4


class PolicyDecision(str, Enum):
    """Policy decision result."""

    ALLOW = "allow"
    REVIEW = "review"
    DENY = "deny"


@dataclass(slots=True)
class PolicyEvaluation:
    """Policy evaluation result."""

    action: str
    decision: PolicyDecision
    requires_approval: bool = False
    reason: str = ""
    id: str = field(default_factory=lambda: str(uuid4()))


class PolicyEngine:
    """Evaluate action risk and approval requirements."""

    def __init__(self, high_risk_keywords: set[str] | None = None) -> None:
        """Create a keyword-based MVP policy engine."""

        self.high_risk_keywords = high_risk_keywords or {"delete", "deploy", "publish", "payment"}

    def evaluate_action(self, action: str) -> PolicyEvaluation:
        """Evaluate an action string."""

        lowered = action.lower()
        if any(keyword in lowered for keyword in self.high_risk_keywords):
            return PolicyEvaluation(
                action=action,
                decision=PolicyDecision.REVIEW,
                requires_approval=True,
                reason="Action matched high-risk policy.",
            )
        return PolicyEvaluation(action=action, decision=PolicyDecision.ALLOW)

    def evaluate_artifact(self, content: object) -> PolicyEvaluation:
        """Evaluate an artifact after execution."""

        return self.evaluate_action(str(content))
