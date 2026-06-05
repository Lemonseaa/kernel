"""Eligibility gate for low-risk autonomous execution."""

from __future__ import annotations

from pydantic import BaseModel

from checkpoint_ai.adapter import AdapterCapabilities, CapabilitySupport
from checkpoint_ai.prompt import PromptProposal, PromptProposalStatus
from checkpoint_ai.shadow import ShadowResult


class EligibilityResult(BaseModel):
    """Decision returned by the auto-execution eligibility gate."""

    eligible: bool
    reasons: list[str]


class AutoExecutionEligibility:
    """Conservative rule gate for V6 low-risk autonomy."""

    def __init__(self, risk_threshold: float = 0.35, magnitude_threshold: float = 0.1) -> None:
        self.risk_threshold = risk_threshold
        self.magnitude_threshold = magnitude_threshold

    def evaluate(
        self,
        proposal: PromptProposal,
        shadow: ShadowResult,
        adapter_capabilities: AdapterCapabilities,
        checkpoint_id: str | None,
        risk_score: float,
        patch_magnitude: float,
    ) -> EligibilityResult:
        """Return whether a proposal is safe enough to enter auto action queue."""

        reasons: list[str] = []
        if proposal.status != PromptProposalStatus.APPROVED:
            reasons.append("proposal_not_approved")
        if not shadow.passed:
            reasons.append("shadow_not_passed")
        if shadow.run_kind == "synthetic":
            reasons.append("synthetic_evidence")
        if shadow.run_kind not in {"historical", "paper", "live"}:
            reasons.append("unsupported_run_kind")
        guardrail_violations = shadow.comparison_result.get("guardrail_violations", [])
        if isinstance(guardrail_violations, list) and guardrail_violations:
            reasons.append("guardrail_violation")
        if risk_score > self.risk_threshold:
            reasons.append("risk_too_high")
        if patch_magnitude > self.magnitude_threshold:
            reasons.append("patch_magnitude_too_large")
        if adapter_capabilities.safe_apply != CapabilitySupport.SUPPORTED:
            reasons.append("safe_apply_unsupported")
        if not checkpoint_id:
            reasons.append("missing_checkpoint")
        return EligibilityResult(eligible=not reasons, reasons=reasons or ["eligible"])
