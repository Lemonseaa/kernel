"""Operator feedback analysis for conservative policy suggestions."""

from __future__ import annotations

from loop_harness.decision import DecisionKind, DecisionLogStore
from loop_harness.prompt import Proposal, ProposalKind, ProposalPatch, ProposalTargetType


class OperatorFeedbackAnalyzer:
    """Convert repeated operator decisions into reviewable policy proposals."""

    def __init__(self, decisions: DecisionLogStore, strong_signal_threshold: float = 0.8) -> None:
        self.decisions = decisions
        self.strong_signal_threshold = strong_signal_threshold

    def suggest_policy_adjustment(
        self,
        scenario_id: str,
        source_type: str,
        min_decisions: int = 5,
    ) -> Proposal | None:
        """Return a policy proposal when operator decisions show a strong pattern."""

        records = [
            record
            for record in self.decisions.list(scenario_id=scenario_id)
            if record.source_type == source_type and record.kind in {DecisionKind.APPROVE, DecisionKind.REJECT}
        ]
        decision_count = len(records)
        if decision_count < min_decisions:
            return None

        approve_count = sum(1 for record in records if record.kind == DecisionKind.APPROVE)
        reject_count = sum(1 for record in records if record.kind == DecisionKind.REJECT)
        approve_rate = approve_count / decision_count
        reject_rate = reject_count / decision_count

        if approve_rate >= self.strong_signal_threshold:
            return self._proposal(
                scenario_id=scenario_id,
                source_type=source_type,
                recommendation="relax",
                rate=approve_rate,
                decision_count=decision_count,
                reason=(
                    f"Operators approved {approve_count}/{decision_count} {source_type} items; "
                    "consider relaxing review threshold for this narrow source type."
                ),
            )
        if reject_rate >= self.strong_signal_threshold:
            return self._proposal(
                scenario_id=scenario_id,
                source_type=source_type,
                recommendation="tighten",
                rate=reject_rate,
                decision_count=decision_count,
                reason=(
                    f"Operators rejected {reject_count}/{decision_count} {source_type} items; "
                    "consider tightening review threshold for this narrow source type."
                ),
            )
        return None

    @staticmethod
    def _proposal(
        scenario_id: str,
        source_type: str,
        recommendation: str,
        rate: float,
        decision_count: int,
        reason: str,
    ) -> Proposal:
        return Proposal(
            scenario_id=scenario_id,
            proposal_kind=ProposalKind.POLICY,
            target_type=ProposalTargetType.POLICY_RULE,
            target_id=f"{source_type}.review_threshold",
            patch=ProposalPatch(
                operation="replace",
                before={"review_threshold": "current"},
                after={"recommendation": recommendation},
            ),
            reason=reason,
            expected_metric="operator_review_load",
            metadata={
                "recommendation": recommendation,
                "decision_count": decision_count,
                "signal_rate": rate,
                "approve_rate": rate if recommendation == "relax" else 1.0 - rate,
                "reject_rate": rate if recommendation == "tighten" else 1.0 - rate,
                "source_type": source_type,
                "requires_human_review": True,
            },
        )
