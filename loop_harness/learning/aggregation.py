"""Observation aggregation for the V7 blackboard."""

from __future__ import annotations

from loop_harness.learning.models import Observation, ObservationSeverity


class ObservationAggregator:
    """Deduplicate and rank observations before proposal generation."""

    def __init__(self, max_items: int = 5) -> None:
        self.max_items = max_items

    def aggregate(self, observations: list[Observation]) -> list[Observation]:
        """Return the highest-signal observations for one tick."""

        deduped: dict[tuple[str, str, str], Observation] = {}
        for observation in observations:
            key = (observation.scenario_id, observation.observation_type.value, observation.title)
            current = deduped.get(key)
            if current is None or _severity_rank(observation.severity) > _severity_rank(current.severity):
                deduped[key] = observation
        ranked = sorted(
            deduped.values(),
            key=lambda item: (_severity_rank(item.severity), item.created_at),
            reverse=True,
        )
        return ranked[: self.max_items]


def _severity_rank(severity: ObservationSeverity) -> int:
    return {
        ObservationSeverity.INFO: 1,
        ObservationSeverity.WARNING: 2,
        ObservationSeverity.CRITICAL: 3,
    }[severity]
