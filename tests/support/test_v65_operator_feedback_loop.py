"""V6.5 operator feedback loop tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from checkpoint_ai.autonomy import OperatorFeedbackAnalyzer
from checkpoint_ai.console import ApprovalInbox
from checkpoint_ai.decision import DecisionKind, DecisionLogStore, DecisionRecord
from checkpoint_ai.prompt import ProposalKind, ProposalStore, ProposalTargetType


class V65OperatorFeedbackLoopTest(unittest.TestCase):
    """Validate feedback-derived policy suggestions."""

    def test_repeated_approvals_create_policy_proposal_visible_in_approval_inbox(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "feedback.db"
            decisions = DecisionLogStore(db_path)
            for index in range(5):
                decisions.record(
                    DecisionRecord(
                        source_id=f"proposal-{index}",
                        source_type="parameter_proposal",
                        kind=DecisionKind.APPROVE,
                        scenario_id="demo-quant",
                        action="approve",
                        comment="This low-risk parameter suggestion was acceptable.",
                    )
                )

            proposal = OperatorFeedbackAnalyzer(decisions).suggest_policy_adjustment(
                scenario_id="demo-quant",
                source_type="parameter_proposal",
                min_decisions=3,
            )
            self.assertIsNotNone(proposal)
            assert proposal is not None
            ProposalStore(db_path).create(proposal)
            inbox_items = ApprovalInbox(db_path).list_items(scenario_id="demo-quant")

        self.assertEqual(proposal.proposal_kind, ProposalKind.POLICY)
        self.assertEqual(proposal.target_type, ProposalTargetType.POLICY_RULE)
        self.assertEqual(proposal.metadata["recommendation"], "relax")
        self.assertEqual(proposal.metadata["decision_count"], 5)
        self.assertEqual(proposal.metadata["approve_rate"], 1.0)
        self.assertEqual([item.item_type for item in inbox_items], ["policy_proposal"])
        self.assertIn("policy", inbox_items[0].title)

    def test_mixed_operator_decisions_do_not_create_policy_proposal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "feedback.db"
            decisions = DecisionLogStore(db_path)
            for index, kind in enumerate(
                [
                    DecisionKind.APPROVE,
                    DecisionKind.REJECT,
                    DecisionKind.APPROVE,
                    DecisionKind.REJECT,
                ]
            ):
                decisions.record(
                    DecisionRecord(
                        source_id=f"proposal-{index}",
                        source_type="parameter_proposal",
                        kind=kind,
                        scenario_id="demo-quant",
                        action=kind.value,
                        comment="Mixed operator feedback should not change policy.",
                    )
                )

            proposal = OperatorFeedbackAnalyzer(decisions).suggest_policy_adjustment(
                scenario_id="demo-quant",
                source_type="parameter_proposal",
                min_decisions=3,
            )

        self.assertIsNone(proposal)


if __name__ == "__main__":
    unittest.main()
