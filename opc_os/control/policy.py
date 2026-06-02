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


class PolicyScope(str, Enum):
    """Policy scope."""

    GLOBAL = "global"
    BUSINESS_LINE = "business_line"


@dataclass(slots=True)
class PolicyRule:
    """A simple keyword policy rule."""

    id: str
    action_keyword: str
    decision: PolicyDecision
    scope: PolicyScope = PolicyScope.GLOBAL
    business_line_id: str | None = None
    reason: str = ""


@dataclass(slots=True)
class PolicyEvaluation:
    """Policy evaluation result."""

    action: str
    decision: PolicyDecision
    requires_approval: bool = False
    reason: str = ""
    policy_id: str | None = None
    id: str = field(default_factory=lambda: str(uuid4()))


class PolicyEngine:
    """Evaluate action risk and approval requirements."""

    def __init__(self, high_risk_keywords: set[str] | None = None) -> None:
        """Create a keyword-based MVP policy engine."""

        self.high_risk_keywords = high_risk_keywords or {"delete", "deploy", "publish", "payment"}
        self._policies: list[PolicyRule] = []

    def add_policy(self, policy: PolicyRule) -> None:
        """Add or replace a policy rule."""

        self._policies = [item for item in self._policies if item.id != policy.id]
        self._policies.append(policy)

    def evaluate_action(self, action: str, business_line_id: str | None = None) -> PolicyEvaluation:
        """Evaluate an action string."""

        lowered = action.lower()
        rule = self._matching_policy(lowered, business_line_id)
        if rule is not None:
            return PolicyEvaluation(
                action=action,
                decision=rule.decision,
                requires_approval=rule.decision == PolicyDecision.REVIEW,
                reason=rule.reason,
                policy_id=rule.id,
            )
        if any(keyword in lowered for keyword in self.high_risk_keywords):
            return PolicyEvaluation(
                action=action,
                decision=PolicyDecision.REVIEW,
                requires_approval=True,
                reason="Action matched high-risk policy.",
                policy_id="keyword_high_risk",
            )
        return PolicyEvaluation(action=action, decision=PolicyDecision.ALLOW)

    def evaluate_artifact(self, content: object, business_line_id: str | None = None) -> PolicyEvaluation:
        """Evaluate an artifact after execution."""

        return self.evaluate_action(str(content), business_line_id=business_line_id)

    def _matching_policy(self, lowered_action: str, business_line_id: str | None) -> PolicyRule | None:
        """Return the highest-priority matching policy."""

        business_line_policies = [
            policy
            for policy in self._policies
            if policy.scope == PolicyScope.BUSINESS_LINE
            and policy.business_line_id == business_line_id
            and policy.action_keyword.lower() in lowered_action
        ]
        if business_line_policies:
            return business_line_policies[-1]
        global_policies = [
            policy
            for policy in self._policies
            if policy.scope == PolicyScope.GLOBAL
            and policy.action_keyword.lower() in lowered_action
        ]
        if global_policies:
            return global_policies[-1]
        return None
