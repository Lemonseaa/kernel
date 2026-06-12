"""V7 dynamic-balance safety rules."""

from __future__ import annotations

from loop_harness.learning.models import ProposalCandidate, SafetyFinding


class SafetyMonitor:
    """Evaluate guardrails, cooldown, budget, and regression signals."""

    def __init__(
        self,
        blocked_targets: set[str] | None = None,
        cooldown_targets: set[str] | None = None,
        remaining_budget: int = 10,
    ) -> None:
        self.blocked_targets = blocked_targets or set()
        self.cooldown_targets = cooldown_targets or set()
        self.remaining_budget = remaining_budget

    def evaluate(self, candidate: ProposalCandidate) -> list[SafetyFinding]:
        """Return explainable findings; callers decide whether to proceed."""

        findings: list[SafetyFinding] = []
        target_id = candidate.proposal.target_id
        if target_id in self.blocked_targets:
            findings.append(self._finding(candidate, "blocked", f"guardrail blocks target {target_id}"))
        if target_id in self.cooldown_targets:
            findings.append(self._finding(candidate, "blocked", f"cooldown active for target {target_id}"))
        if self.remaining_budget <= 0:
            findings.append(self._finding(candidate, "blocked", "optimization budget exhausted"))
        if candidate.proposal.patch.operation in {"compress", "refactor"}:
            findings.append(self._finding(candidate, "warning", "refactor proposal requires stronger evidence"))
        return findings

    @staticmethod
    def _finding(candidate: ProposalCandidate, severity: str, reason: str) -> SafetyFinding:
        return SafetyFinding(
            business_line_id=candidate.business_line_id,
            scenario_id=candidate.scenario_id,
            proposal_id=candidate.proposal.id,
            severity=severity,
            reason=reason,
            source_ids=[candidate.id, *candidate.source_ids],
        )
