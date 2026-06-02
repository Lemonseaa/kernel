"""Built-in policy rules."""

from __future__ import annotations

from checkpoint_ai.control.policy import PolicyDecision, PolicyRule, PolicyScope


def builtin_policies() -> list[PolicyRule]:
    """Return built-in global policies."""

    return [
        PolicyRule(
            id="high_risk_require_approval",
            action_keyword="delete",
            decision=PolicyDecision.REVIEW,
            scope=PolicyScope.GLOBAL,
            reason="High-risk action requires approval.",
        ),
        PolicyRule(
            id="publish_require_approval",
            action_keyword="publish",
            decision=PolicyDecision.REVIEW,
            scope=PolicyScope.GLOBAL,
            reason="Publish action requires approval.",
        ),
    ]
