"""Validation summaries for V7 shadow/replay outcomes."""

from __future__ import annotations

from checkpoint_ai.learning.models import (
    ProposalCandidate,
    ValidationSummary,
    validation_from_comparison,
)
from checkpoint_ai.metrics import ComparisonResult


class Validator:
    """Explain whether a shadow/replay candidate improved over baseline."""

    def validate(
        self,
        candidate: ProposalCandidate,
        shadow_result_id: str,
        comparison: ComparisonResult,
    ) -> ValidationSummary:
        """Return a user-readable validation summary."""

        return validation_from_comparison(candidate, shadow_result_id, comparison)
