"""Proposal ranking and conflict detection."""

from __future__ import annotations

from loop_harness.learning.models import ProposalCandidate
from loop_harness.prompt import ProposalKind


class ProposalRanker:
    """Rank candidates by small-change safety and verifiability."""

    def rank(self, candidates: list[ProposalCandidate]) -> list[ProposalCandidate]:
        """Return candidates with scores, highest first."""

        ranked: list[ProposalCandidate] = []
        for candidate in candidates:
            score = 0.5
            if candidate.proposal.patch.operation == "replace":
                score += 0.2
            if candidate.proposal.proposal_kind == ProposalKind.PARAMETER:
                score += 0.1
            if candidate.proposal.expected_metric.strip():
                score += 0.1
            candidate.score = round(score - candidate.risk_hint, 6)
            ranked.append(candidate)
        return sorted(ranked, key=lambda item: item.score, reverse=True)


class ConflictDetector:
    """Keep only one candidate per target per learning tick."""

    def filter_conflicts(self, candidates: list[ProposalCandidate]) -> list[ProposalCandidate]:
        """Drop lower-ranked candidates that touch the same target."""

        seen: set[str] = set()
        filtered: list[ProposalCandidate] = []
        for candidate in candidates:
            if candidate.proposal.target_id in seen:
                continue
            seen.add(candidate.proposal.target_id)
            filtered.append(candidate)
        return filtered
