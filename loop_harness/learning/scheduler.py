"""Shadow/replay scheduling for V7."""

from __future__ import annotations

from loop_harness.learning.models import ProposalCandidate, ShadowReplayJob


class ShadowReplayScheduler:
    """Schedule validation jobs without applying proposals."""

    def schedule(self, candidate: ProposalCandidate) -> ShadowReplayJob:
        """Create a pending shadow/replay job."""

        return ShadowReplayJob(
            business_line_id=candidate.business_line_id,
            scenario_id=candidate.scenario_id,
            proposal_id=candidate.proposal.id,
            candidate_id=candidate.id,
            apply_requested=False,
            source_ids=[candidate.id, *candidate.source_ids],
        )
