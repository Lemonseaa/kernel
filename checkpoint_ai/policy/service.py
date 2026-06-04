"""Policy service that gates shadow execution and proposal application."""

from __future__ import annotations

from typing import Protocol

from checkpoint_ai.policy.models import PolicyLevel, PolicyProcessResult
from checkpoint_ai.policy.scenario_policy import ScenarioPolicy
from checkpoint_ai.prompt import (
    PromptProposal,
    PromptProposalStatus,
    PromptProposalStore,
    PromptVersionStore,
)


class ShadowRunner(Protocol):
    """Minimal V2.3 shadow runner contract."""

    def run(self, proposal: PromptProposal) -> bool:
        """Return whether the proposal passed shadow."""


class ScenarioPolicyService:
    """Process prompt proposals through policy before shadow."""

    def __init__(
        self,
        policy: ScenarioPolicy,
        proposals: PromptProposalStore,
        versions: PromptVersionStore,
        shadow_runner: ShadowRunner,
    ) -> None:
        self.policy = policy
        self.proposals = proposals
        self.versions = versions
        self.shadow_runner = shadow_runner

    def process(self, proposal_id: str) -> PolicyProcessResult:
        """Evaluate policy, optionally run shadow, and update proposal state."""

        proposal = self.proposals.get(proposal_id)
        if proposal is None:
            raise KeyError(f"PromptProposal not found: {proposal_id}")

        decision = self.policy.evaluate(proposal)
        self.proposals.update_metadata(
            proposal_id,
            {
                "policy_level": decision.level.value,
                "policy_reason": decision.reason,
            },
        )

        if decision.level == PolicyLevel.BLOCKED:
            self.proposals.update_metadata(proposal_id, {"shadow_run": False})
            self.proposals.update_status(proposal_id, PromptProposalStatus.REJECTED)
            return PolicyProcessResult(
                proposal_id=proposal_id,
                level=decision.level,
                policy_reason=decision.reason,
                shadow_required=False,
                shadow_ran=False,
                shadow_passed=None,
                action="blocked",
            )

        shadow_passed = self.shadow_runner.run(proposal)
        self.proposals.update_metadata(
            proposal_id,
            {
                "shadow_required": True,
                "shadow_run": True,
                "shadow_passed": shadow_passed,
            },
        )
        if not shadow_passed:
            self.proposals.update_status(proposal_id, PromptProposalStatus.REJECTED)
            return PolicyProcessResult(
                proposal_id=proposal_id,
                level=decision.level,
                policy_reason=decision.reason,
                shadow_required=True,
                shadow_ran=True,
                shadow_passed=False,
                action="shadow_failed",
            )

        if decision.level == PolicyLevel.AUTO:
            self._apply_auto_patch(proposal)
            self.proposals.update_status(proposal_id, PromptProposalStatus.APPLIED)
            return PolicyProcessResult(
                proposal_id=proposal_id,
                level=decision.level,
                policy_reason=decision.reason,
                shadow_required=True,
                shadow_ran=True,
                shadow_passed=True,
                action="auto_applied",
            )

        self.proposals.update_metadata(proposal_id, {"awaiting_human_confirmation": True})
        self.proposals.update_status(proposal_id, PromptProposalStatus.APPROVED)
        return PolicyProcessResult(
            proposal_id=proposal_id,
            level=decision.level,
            policy_reason=decision.reason,
            shadow_required=True,
            shadow_ran=True,
            shadow_passed=True,
            action="awaiting_human_confirmation",
        )

    def _apply_auto_patch(self, proposal: PromptProposal) -> None:
        latest = self.versions.get_latest(proposal.scenario_id, proposal.agent_id)
        slots = dict(latest.slots) if latest is not None else {}
        slot = proposal.patch.slot
        if proposal.patch.operation in {"replace", "add", "compress"}:
            slots[slot] = proposal.patch.after
        elif proposal.patch.operation == "remove":
            slots.pop(slot, None)
        else:
            raise ValueError(f"Unsupported auto patch operation: {proposal.patch.operation}")
        self.versions.save_version(
            scenario_id=proposal.scenario_id,
            agent_id=proposal.agent_id,
            slots=slots,
            reason=f"Applied proposal {proposal.id}: {proposal.reason}",
        )
