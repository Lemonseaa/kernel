"""SQLite storage for Experiment Ledger."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from loop_harness.experiment.models import Experiment, ExperimentStatus


class SQLiteExperimentStorage:
    """Persist experiment records in SQLite."""

    def __init__(self, path: str | Path) -> None:
        """Create or open the experiment database."""

        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
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
        """Create the experiments table and indexes."""

        with self._connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS experiments (
                    id TEXT PRIMARY KEY,
                    business_line_id TEXT,
                    hypothesis TEXT NOT NULL,
                    baseline_id TEXT,
                    action TEXT NOT NULL,
                    before_metrics TEXT NOT NULL,
                    after_metrics TEXT NOT NULL,
                    result_summary TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_experiments_bl ON experiments (business_line_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_experiments_status ON experiments (status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_experiments_created ON experiments (created_at)")

    def save(self, experiment: Experiment) -> str:
        """Insert or update one experiment."""

        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO experiments (
                    id, business_line_id, hypothesis, baseline_id, action,
                    before_metrics, after_metrics, result_summary, status,
                    created_at, updated_at, metadata
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    business_line_id=excluded.business_line_id,
                    hypothesis=excluded.hypothesis,
                    baseline_id=excluded.baseline_id,
                    action=excluded.action,
                    before_metrics=excluded.before_metrics,
                    after_metrics=excluded.after_metrics,
                    result_summary=excluded.result_summary,
                    status=excluded.status,
                    created_at=excluded.created_at,
                    updated_at=excluded.updated_at,
                    metadata=excluded.metadata
                """,
                self._to_row(experiment),
            )
        return experiment.id

    def get(self, experiment_id: str) -> Experiment | None:
        """Return one experiment by id."""

        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM experiments WHERE id = ?", (experiment_id,)).fetchone()
        return None if row is None else self._from_row(row)

    def list(
        self,
        business_line_id: str | None = None,
        status: ExperimentStatus | None = None,
    ) -> list[Experiment]:
        """List experiments ordered by creation time."""

        clauses: list[str] = []
        params: list[Any] = []
        if business_line_id is not None:
            clauses.append("business_line_id = ?")
            params.append(business_line_id)
        if status is not None:
            clauses.append("status = ?")
            params.append(status.value)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = f"SELECT * FROM experiments {where} ORDER BY created_at, rowid"
        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(sql, tuple(params)).fetchall()
        return [self._from_row(row) for row in rows]

    @staticmethod
    def _to_row(experiment: Experiment) -> tuple[Any, ...]:
        return (
            experiment.id,
            experiment.business_line_id,
            experiment.hypothesis,
            experiment.baseline_id,
            experiment.action,
            json.dumps(experiment.before_metrics, ensure_ascii=False, default=str),
            json.dumps(experiment.after_metrics, ensure_ascii=False, default=str),
            experiment.result_summary,
            experiment.status.value,
            experiment.created_at.isoformat(),
            experiment.updated_at.isoformat(),
            json.dumps(experiment.metadata, ensure_ascii=False, default=str),
        )

    @staticmethod
    def _from_row(row: sqlite3.Row) -> Experiment:
        return Experiment(
            id=row["id"],
            business_line_id=row["business_line_id"],
            hypothesis=row["hypothesis"],
            baseline_id=row["baseline_id"],
            action=row["action"],
            before_metrics=json.loads(row["before_metrics"]),
            after_metrics=json.loads(row["after_metrics"]),
            result_summary=row["result_summary"],
            status=ExperimentStatus(row["status"]),
            created_at=datetime.fromisoformat(row["created_at"]).astimezone(UTC),
            updated_at=datetime.fromisoformat(row["updated_at"]).astimezone(UTC),
            metadata=json.loads(row["metadata"]),
        )
