"""Hard-coded V2.3 scenario policy."""

from __future__ import annotations

from checkpoint_ai.policy.models import PolicyDecision, PolicyLevel
from checkpoint_ai.prompt import (
    PromptProposal,
    PromptSlot,
    Proposal,
    ProposalKind,
    ProposalTargetType,
)


class ScenarioPolicy:
    """Classify prompt proposals before shadow execution."""

    def evaluate(self, proposal: PromptProposal) -> PolicyDecision:
        """Classify a proposal as AUTO, APPROVAL, or BLOCKED."""

        patch = proposal.patch
        if patch.operation == "refactor":
            return PolicyDecision(
                proposal_id=proposal.id,
                level=PolicyLevel.BLOCKED,
                reason="refactor proposals are blocked in V2.3 and require a later explicit workflow",
            )
        if patch.slot in {PromptSlot.GOAL, PromptSlot.TOOLS_POLICY}:
            return PolicyDecision(
                proposal_id=proposal.id,
                level=PolicyLevel.BLOCKED,
                reason=f"{patch.slot.value} changes are high risk and blocked in V2.3",
            )
        if patch.slot in {PromptSlot.ROLE, PromptSlot.CONSTRAINTS}:
            return PolicyDecision(
                proposal_id=proposal.id,
                level=PolicyLevel.APPROVAL,
                reason=f"{patch.slot.value} changes require human approval after shadow",
            )
        return PolicyDecision(
            proposal_id=proposal.id,
            level=PolicyLevel.AUTO,
            reason=f"{patch.slot.value} {patch.operation} is a bounded low-risk patch",
        )

    def evaluate_proposal(self, proposal: Proposal) -> PolicyDecision:
        """Classify a generic proposal using V2.10 risk context."""

        run_kind = str(proposal.metadata.get("run_kind", "synthetic"))
        magnitude = self._magnitude(proposal)
        if proposal.proposal_kind == ProposalKind.DEPLOYMENT or run_kind == "live":
            return PolicyDecision(
                proposal_id=proposal.id,
                level=PolicyLevel.BLOCKED,
                reason="live deployment proposals are blocked before explicit human deployment workflow",
            )
        if proposal.patch.operation == "refactor":
            return PolicyDecision(
                proposal_id=proposal.id,
                level=PolicyLevel.BLOCKED,
                reason="refactor proposals remain blocked before a dedicated refactor workflow",
            )
        if (
            proposal.proposal_kind in {ProposalKind.STRATEGY, ProposalKind.PARAMETER}
            and proposal.target_type == ProposalTargetType.STRATEGY_PARAM
            and magnitude <= 0.1
        ):
            return PolicyDecision(
                proposal_id=proposal.id,
                level=PolicyLevel.AUTO,
                reason="small non-live strategy parameter adjustment can run shadow and auto-apply",
            )
        if proposal.proposal_kind in {ProposalKind.STRATEGY, ProposalKind.PARAMETER}:
            return PolicyDecision(
                proposal_id=proposal.id,
                level=PolicyLevel.APPROVAL,
                reason="strategy or parameter proposal requires human confirmation after shadow",
            )
        if proposal.proposal_kind == ProposalKind.PROMPT:
            return PolicyDecision(
                proposal_id=proposal.id,
                level=PolicyLevel.APPROVAL,
                reason="generic prompt proposal requires human confirmation unless routed through legacy prompt policy",
            )
        return PolicyDecision(
            proposal_id=proposal.id,
            level=PolicyLevel.APPROVAL,
            reason="unknown proposal kind defaults to approval",
        )

    @staticmethod
    def _magnitude(proposal: Proposal) -> float:
        value = proposal.metadata.get("magnitude", 1.0)
        if isinstance(value, int | float):
            return float(value)
        return 1.0
