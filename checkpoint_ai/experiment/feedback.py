"""Feedback collection for experiments."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from checkpoint_ai.experiment.ledger import ExperimentLedger


class FeedbackSource(str, Enum):
    """Feedback source."""

    INTERNAL = "internal"
    EXTERNAL = "external"
    MANUAL = "manual"


class Feedback(BaseModel):
    """Feedback signal associated with an experiment."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    experiment_id: str | None = None
    source: FeedbackSource
    signal_type: str
    value: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    context: dict[str, Any] = Field(default_factory=dict)


class FeedbackCollector:
    """统一反馈采集。"""

    def __init__(self, storage: str | Path) -> None:
        """Create a collector backed by SQLite."""

        self.path = Path(storage)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.ledger = ExperimentLedger(self.path)
        self._init_schema()

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_schema(self) -> None:
        """Create feedback storage."""

        with self._connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS feedback (
                    id TEXT PRIMARY KEY,
                    experiment_id TEXT,
                    source TEXT NOT NULL,
                    signal_type TEXT NOT NULL,
                    value REAL NOT NULL,
                    timestamp TEXT NOT NULL,
                    context TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_feedback_experiment ON feedback (experiment_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_feedback_source ON feedback (source)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_feedback_signal ON feedback (signal_type)")

    def add(self, feedback: Feedback) -> str:
        """Add feedback and return its id."""

        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO feedback (
                    id, experiment_id, source, signal_type, value, timestamp, context
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    experiment_id=excluded.experiment_id,
                    source=excluded.source,
                    signal_type=excluded.signal_type,
                    value=excluded.value,
                    timestamp=excluded.timestamp,
                    context=excluded.context
                """,
                (
                    feedback.id,
                    feedback.experiment_id,
                    feedback.source.value,
                    feedback.signal_type,
                    feedback.value,
                    feedback.timestamp.isoformat(),
                    json.dumps(feedback.context, ensure_ascii=False, default=str),
                ),
            )
        return feedback.id

    def list(
        self,
        experiment_id: str | None = None,
        source: FeedbackSource | None = None,
    ) -> list[Feedback]:
        """List feedback signals."""

        clauses: list[str] = []
        params: list[Any] = []
        if experiment_id is not None:
            clauses.append("experiment_id = ?")
            params.append(experiment_id)
        if source is not None:
            clauses.append("source = ?")
            params.append(source.value)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = f"SELECT * FROM feedback {where} ORDER BY timestamp, rowid"
        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(sql, tuple(params)).fetchall()
        return [self._from_row(row) for row in rows]

    def apply_to_experiment(self, experiment_id: str) -> dict[str, Any]:
        """Aggregate feedback and update the experiment's after_metrics."""

        experiment = self.ledger.get(experiment_id)
        if experiment is None:
            raise KeyError(f"Experiment not found: {experiment_id}")
        feedback_items = self.list(experiment_id=experiment_id)
        after_metrics = dict(experiment.after_metrics)
        for feedback in feedback_items:
            after_metrics[feedback.signal_type] = feedback.value
        metrics = self._metric_summary(experiment.before_metrics, after_metrics)
        result_summary = self._result_summary(metrics)
        self.ledger.update(
            experiment_id,
            after_metrics=after_metrics,
            result_summary=result_summary,
        )
        return {
            "experiment_id": experiment_id,
            "feedback_count": len(feedback_items),
            "before_metrics": experiment.before_metrics,
            "after_metrics": after_metrics,
            "metrics": metrics,
            "result_summary": result_summary,
        }

    @staticmethod
    def _metric_summary(
        before_metrics: dict[str, Any],
        after_metrics: dict[str, Any],
    ) -> dict[str, dict[str, Any]]:
        metric_names = sorted(set(before_metrics) | set(after_metrics))
        result: dict[str, dict[str, Any]] = {}
        for name in metric_names:
            before = before_metrics.get(name)
            after = after_metrics.get(name)
            delta = float(after - before) if isinstance(before, int | float) and isinstance(after, int | float) else None
            result[name] = {
                "before": before,
                "after": after,
                "delta": delta,
                "improved": None if delta is None else delta > 0,
            }
        return result

    @staticmethod
    def _result_summary(metrics: dict[str, dict[str, Any]]) -> str:
        changed = [
            f"{name}: {metric['before']} -> {metric['after']} (delta={metric['delta']})"
            for name, metric in metrics.items()
            if metric["delta"] is not None
        ]
        if not changed:
            return "反馈已记录，但没有可计算的数值变化。"
        return "反馈已应用；" + "；".join(changed)

    @staticmethod
    def _from_row(row: sqlite3.Row) -> Feedback:
        return Feedback(
            id=row["id"],
            experiment_id=row["experiment_id"],
            source=FeedbackSource(row["source"]),
            signal_type=row["signal_type"],
            value=row["value"],
            timestamp=datetime.fromisoformat(row["timestamp"]).astimezone(UTC),
            context=json.loads(row["context"]),
        )
