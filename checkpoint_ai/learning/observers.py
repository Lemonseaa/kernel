"""Observer hive implementations for V7."""

from __future__ import annotations

from typing import Any

from checkpoint_ai.decision import DecisionKind, DecisionLogStore
from checkpoint_ai.learning.models import Observation, ObservationSeverity, ObservationType
from checkpoint_ai.logs import SummaryLogStore


class MetricObserver:
    """Find metric drift from summary logs."""

    def __init__(
        self,
        summary_store: SummaryLogStore,
        thresholds: dict[str, float] | None = None,
    ) -> None:
        self.summary_store = summary_store
        self.thresholds = thresholds or {}

    def observe(self, scenario_id: str, business_line_id: str | None = None) -> list[Observation]:
        """Return metric observations for one scenario."""

        observations: list[Observation] = []
        for row in self.summary_store.query_by_scenario(scenario_id):
            metrics = row.get("metrics", {})
            if not isinstance(metrics, dict):
                continue
            for metric, threshold in self.thresholds.items():
                value = metrics.get(metric)
                if isinstance(value, int | float) and float(value) < threshold:
                    observations.append(
                        Observation(
                            business_line_id=business_line_id or _business_line_from_row(row),
                            scenario_id=scenario_id,
                            observation_type=ObservationType.METRIC_ANOMALY,
                            severity=ObservationSeverity.WARNING,
                            title=f"{metric} below threshold",
                            summary=f"{metric}={value} is below threshold={threshold}.",
                            source_ids=[str(row["run_id"])],
                            metadata={
                                "metric": metric,
                                "value": value,
                                "threshold": threshold,
                                "target_id": f"strategy.{metric}",
                            },
                        )
                    )
        return observations


class DecisionObserver:
    """Find repeated rejection or blocking patterns from decision logs."""

    def __init__(self, decision_store: DecisionLogStore) -> None:
        self.decision_store = decision_store

    def observe(self, scenario_id: str, business_line_id: str | None = None) -> list[Observation]:
        """Return decision-pattern observations for one scenario."""

        observations: list[Observation] = []
        for record in self.decision_store.list(scenario_id=scenario_id):
            if record.kind not in {DecisionKind.REJECT, DecisionKind.BLOCKED, DecisionKind.ERROR}:
                continue
            observations.append(
                Observation(
                    business_line_id=business_line_id or str(record.details.get("business_line_id", "default")),
                    scenario_id=scenario_id,
                    observation_type=ObservationType.DECISION_PATTERN,
                    severity=ObservationSeverity.WARNING,
                    title=f"Decision friction: {record.kind.value}",
                    summary=record.comment,
                    source_ids=[record.id, record.source_id],
                    metadata={"source_type": record.source_type, "action": record.action},
                )
            )
        return observations


def _business_line_from_row(row: dict[str, Any]) -> str:
    metadata = row.get("metadata")
    if isinstance(metadata, dict) and isinstance(metadata.get("business_line_id"), str):
        return str(metadata["business_line_id"])
    return "default"
