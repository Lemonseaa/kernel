"""Simple baseline comparison for experiments."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from checkpoint_ai.experiment.baseline import BaselineManager
from checkpoint_ai.experiment.ledger import ExperimentLedger


class CompareResult(BaseModel):
    """Simple comparison result."""

    baseline_metrics: dict[str, Any] = Field(default_factory=dict)
    experiment_metrics: dict[str, Any] = Field(default_factory=dict)
    delta: dict[str, float | None] = Field(default_factory=dict)
    improvement: dict[str, float | None] = Field(default_factory=dict)
    winner: str
    summary: str


class SimpleComparer:
    """简单对比器。"""

    _LOWER_IS_BETTER_HINTS = ("latency", "cost", "error", "loss", "drawdown", "timeout", "duration")

    def __init__(self, storage: str | Path) -> None:
        """Create a comparer using the shared SQLite database."""

        self.path = Path(storage)
        self.ledger = ExperimentLedger(self.path)
        self.baselines = BaselineManager(self.path)

    def compare(self, experiment_id: str, baseline_id: str | None = None) -> CompareResult:
        """对比实验与基线。"""

        experiment = self.ledger.get(experiment_id)
        if experiment is None:
            raise KeyError(f"Experiment not found: {experiment_id}")
        baseline = (
            self.baselines.get(baseline_id)
            if baseline_id is not None
            else self.baselines.get_active(experiment.business_line_id)
        )
        if baseline is None:
            raise KeyError("Active baseline not found")

        baseline_metrics = baseline.metrics
        experiment_metrics = experiment.after_metrics
        metric_names = sorted(set(baseline_metrics) | set(experiment_metrics))
        delta: dict[str, float | None] = {}
        improvement: dict[str, float | None] = {}
        score = 0
        for name in metric_names:
            baseline_value = baseline_metrics.get(name)
            experiment_value = experiment_metrics.get(name)
            metric_delta = self._delta(baseline_value, experiment_value)
            delta[name] = metric_delta
            improvement[name] = self._improvement(name, baseline_value, experiment_value)
            score += self._metric_score(name, baseline_value, experiment_value)

        winner = "experiment" if score > 0 else "baseline" if score < 0 else "tie"
        return CompareResult(
            baseline_metrics=baseline_metrics,
            experiment_metrics=experiment_metrics,
            delta=delta,
            improvement=improvement,
            winner=winner,
            summary=self._summary(winner, delta),
        )

    def is_better(self, result: CompareResult, min_delta: float = 0.0) -> bool:
        """判断是否明显更好。"""

        if result.winner != "experiment":
            return False
        numeric_improvements = [value for value in result.improvement.values() if value is not None]
        return any(value > min_delta for value in numeric_improvements)

    @staticmethod
    def _delta(baseline_value: Any, experiment_value: Any) -> float | None:
        if isinstance(baseline_value, int | float) and isinstance(experiment_value, int | float):
            return float(experiment_value - baseline_value)
        return None

    @classmethod
    def _improvement(cls, name: str, baseline_value: Any, experiment_value: Any) -> float | None:
        metric_delta = cls._delta(baseline_value, experiment_value)
        if metric_delta is None or not isinstance(baseline_value, int | float) or baseline_value == 0:
            return None
        direction_delta = -metric_delta if cls._lower_is_better(name) else metric_delta
        return float(direction_delta / abs(baseline_value))

    @classmethod
    def _metric_score(cls, name: str, baseline_value: Any, experiment_value: Any) -> int:
        improvement = cls._improvement(name, baseline_value, experiment_value)
        if improvement is None or improvement == 0:
            return 0
        return 1 if improvement > 0 else -1

    @classmethod
    def _lower_is_better(cls, name: str) -> bool:
        normalized = name.lower()
        return any(hint in normalized for hint in cls._LOWER_IS_BETTER_HINTS)

    @staticmethod
    def _summary(winner: str, delta: dict[str, float | None]) -> str:
        changed = [f"{name}: delta={value}" for name, value in delta.items() if value is not None]
        if not changed:
            return f"winner={winner}; no numeric metric changes"
        return f"winner={winner}; " + "; ".join(changed)
