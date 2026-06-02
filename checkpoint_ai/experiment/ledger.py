"""Experiment Ledger service."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from checkpoint_ai.experiment.models import Experiment, ExperimentStatus
from checkpoint_ai.experiment.storage import SQLiteExperimentStorage


class ExperimentLedger:
    """实验账本。"""

    def __init__(self, storage: SQLiteExperimentStorage | str | Path) -> None:
        """Create a ledger from storage or a SQLite path."""

        self.storage = storage if isinstance(storage, SQLiteExperimentStorage) else SQLiteExperimentStorage(storage)

    def create(self, experiment: Experiment) -> str:
        """创建实验。"""

        now = datetime.now(UTC)
        if experiment.created_at is None:
            experiment.created_at = now
        experiment.updated_at = now
        return self.storage.save(experiment)

    def update(self, id: str, **kwargs: Any) -> bool:
        """更新实验。"""

        experiment = self.get(id)
        if experiment is None:
            return False
        update_data = dict(kwargs)
        update_data["updated_at"] = datetime.now(UTC)
        updated = experiment.model_copy(update=update_data)
        self.storage.save(updated)
        return True

    def get(self, id: str) -> Experiment | None:
        """获取实验。"""

        return self.storage.get(id)

    def list(
        self,
        business_line_id: str | None = None,
        status: ExperimentStatus | None = None,
    ) -> list[Experiment]:
        """列出实验。"""

        return self.storage.list(business_line_id=business_line_id, status=status)

    def compare(self, id1: str, id2: str) -> dict[str, Any]:
        """对比两个实验。"""

        left = self.get(id1)
        right = self.get(id2)
        if left is None:
            raise KeyError(f"Experiment not found: {id1}")
        if right is None:
            raise KeyError(f"Experiment not found: {id2}")
        metric_names = sorted(set(left.after_metrics) | set(right.after_metrics))
        metrics: dict[str, dict[str, Any]] = {}
        for name in metric_names:
            left_value = left.after_metrics.get(name)
            right_value = right.after_metrics.get(name)
            metrics[name] = {
                "left": left_value,
                "right": right_value,
                "delta": self._numeric_delta(left_value, right_value),
                "improved": self._improved(left_value, right_value),
            }
        return {
            "left_id": left.id,
            "right_id": right.id,
            "left_action": left.action,
            "right_action": right.action,
            "metrics": metrics,
        }

    def set_baseline(self, experiment_id: str) -> str:
        """将实验结果设为新基线。"""

        experiment = self.get(experiment_id)
        if experiment is None:
            raise KeyError(f"Experiment not found: {experiment_id}")
        from checkpoint_ai.experiment.baseline import BaselineManager

        return BaselineManager(self._storage_path()).create(
            experiment.after_metrics,
            name=f"baseline-from-{experiment_id[:8]}",
            business_line_id=experiment.business_line_id,
            experiment_id=experiment_id,
        )

    def compare_to_baseline(self, experiment_id: str) -> Any:
        """与当前基线对比。"""

        from checkpoint_ai.experiment.compare import SimpleComparer

        return SimpleComparer(self._storage_path()).compare(experiment_id)

    def generate_summary(self, id: str) -> str:
        """生成实验摘要，回答7个问题。"""

        experiment = self.get(id)
        if experiment is None:
            raise KeyError(f"Experiment not found: {id}")
        baseline = self.get(experiment.baseline_id) if experiment.baseline_id else None
        changed = self._result_label(experiment)
        storage_path = getattr(self.storage, "path", "memory")
        baseline_answer = (
            f"{baseline.id} ({baseline.action})"
            if baseline is not None
            else (experiment.baseline_id or "无基线，这是基线实验")
        )
        return "\n".join(
            [
                f"Experiment ID: {experiment.id}",
                f"BusinessLine: {experiment.business_line_id or 'default'}",
                f"Status: {experiment.status.value}",
                f"为什么做这个实验？{experiment.hypothesis}",
                f"基线是什么？{baseline_answer}",
                f"改了什么？{experiment.action}",
                f"改之前多少？{experiment.before_metrics}",
                f"改之后多少？{experiment.after_metrics}",
                f"有没有变好？{changed}。{experiment.result_summary}",
                f"记录在哪里？{storage_path} / experiments / {experiment.id}",
            ]
        )

    @staticmethod
    def _numeric_delta(left: Any, right: Any) -> float | None:
        if isinstance(left, int | float) and isinstance(right, int | float):
            return float(right - left)
        return None

    @staticmethod
    def _improved(left: Any, right: Any) -> bool | None:
        if isinstance(left, int | float) and isinstance(right, int | float):
            return right > left
        return None

    @classmethod
    def _result_label(cls, experiment: Experiment) -> str:
        deltas = [
            cls._numeric_delta(experiment.before_metrics.get(name), experiment.after_metrics.get(name))
            for name in sorted(set(experiment.before_metrics) | set(experiment.after_metrics))
        ]
        numeric_deltas = [delta for delta in deltas if delta is not None]
        if not numeric_deltas:
            return "无法用数值判断"
        if any(delta > 0 for delta in numeric_deltas):
            return "是"
        if any(delta < 0 for delta in numeric_deltas):
            return "否"
        return "没有变化"

    def _storage_path(self) -> Path:
        path = getattr(self.storage, "path", None)
        if path is None:
            raise RuntimeError("ExperimentLedger baseline operations require SQLite storage")
        return Path(path)
