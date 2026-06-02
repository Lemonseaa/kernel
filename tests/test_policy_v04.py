"""V0.4 policy inheritance tests."""

from __future__ import annotations

import unittest

from checkpoint_ai.control import PolicyDecision, PolicyEngine, PolicyRule, PolicyScope


class PolicyV04Test(unittest.TestCase):
    """Validate global and BusinessLine policy precedence."""

    def test_global_policy_applies_to_all_business_lines(self) -> None:
        engine = PolicyEngine()
        engine.add_policy(
            PolicyRule(
                id="publish_require_approval",
                action_keyword="publish",
                decision=PolicyDecision.REVIEW,
                scope=PolicyScope.GLOBAL,
                reason="Publish requires approval.",
            )
        )

        decision = engine.evaluate_action("publish content", business_line_id="bl-a")

        self.assertEqual(decision.decision, PolicyDecision.REVIEW)
        self.assertTrue(decision.requires_approval)
        self.assertEqual(decision.policy_id, "publish_require_approval")

    def test_business_line_policy_overrides_global_policy(self) -> None:
        engine = PolicyEngine()
        engine.add_policy(
            PolicyRule(
                id="global_publish_review",
                action_keyword="publish",
                decision=PolicyDecision.REVIEW,
                scope=PolicyScope.GLOBAL,
            )
        )
        engine.add_policy(
            PolicyRule(
                id="bl_publish_allow",
                action_keyword="publish",
                decision=PolicyDecision.ALLOW,
                scope=PolicyScope.BUSINESS_LINE,
                business_line_id="bl-a",
            )
        )

        decision_a = engine.evaluate_action("publish content", business_line_id="bl-a")
        decision_b = engine.evaluate_action("publish content", business_line_id="bl-b")

        self.assertEqual(decision_a.decision, PolicyDecision.ALLOW)
        self.assertFalse(decision_a.requires_approval)
        self.assertEqual(decision_a.policy_id, "bl_publish_allow")
        self.assertEqual(decision_b.decision, PolicyDecision.REVIEW)
        self.assertEqual(decision_b.policy_id, "global_publish_review")


if __name__ == "__main__":
    unittest.main()
