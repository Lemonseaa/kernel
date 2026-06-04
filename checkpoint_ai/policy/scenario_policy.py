"""Hard-coded V2.3 scenario policy."""

from __future__ import annotations

from checkpoint_ai.policy.models import PolicyDecision, PolicyLevel
from checkpoint_ai.prompt import PromptProposal, PromptSlot


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
