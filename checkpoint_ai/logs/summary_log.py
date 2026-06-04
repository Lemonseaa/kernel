"""Summary run log storage for V2.1 scenarios."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from checkpoint_ai.adapter import AgentRunResult


class SummaryLogStore:
    """Persist concise run summaries and metrics."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path is not None else None
        self._memory: dict[str, dict[str, Any]] = {}
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._init_schema()

    def save(self, result: AgentRunResult) -> None:
        """Save metrics and value summary, or a failed summary."""

        row = self._to_record(result)
        if self.path is None:
            self._memory[result.run_id] = row
            return
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO summary_logs (
                    run_id, scenario_id, task, status, metrics, value_summary,
                    error_type, failed_summary, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(run_id) DO UPDATE SET
                    scenario_id=excluded.scenario_id,
                    task=excluded.task,
                    status=excluded.status,
                    metrics=excluded.metrics,
                    value_summary=excluded.value_summary,
                    error_type=excluded.error_type,
                    failed_summary=excluded.failed_summary,
                    created_at=excluded.created_at
                """,
                (
                    row["run_id"],
                    row["scenario_id"],
                    row["task"],
                    row["status"],
                    json.dumps(row["metrics"], ensure_ascii=False, default=str),
                    row.get("value_summary"),
                    row.get("error_type"),
                    row.get("failed_summary"),
                    row["created_at"],
                ),
            )

    def get(self, run_id: str) -> dict[str, Any] | None:
        """Return one summary log by run id."""

        if self.path is None:
            return self._memory.get(run_id)
        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM summary_logs WHERE run_id = ?", (run_id,)).fetchone()
        return None if row is None else self._from_row(row)

    def query_by_scenario(self, scenario_id: str) -> list[dict[str, Any]]:
        """Return summary logs for one scenario."""

        if self.path is None:
            return [row for row in self._memory.values() if row["scenario_id"] == scenario_id]
        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM summary_logs WHERE scenario_id = ? ORDER BY created_at, rowid",
                (scenario_id,),
            ).fetchall()
        return [self._from_row(row) for row in rows]

    @staticmethod
    def _to_record(result: AgentRunResult) -> dict[str, Any]:
        record: dict[str, Any] = {
            "run_id": result.run_id,
            "scenario_id": result.scenario_id,
            "task": result.task,
            "status": result.status,
            "metrics": result.metrics,
            "created_at": datetime.now(UTC).isoformat(),
        }
        if result.status == "success":
            record["value_summary"] = result.value_summary
        else:
            record["error_type"] = result.error_type
            record["failed_summary"] = result.value_summary or result.answer
        return record

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        if self.path is None:
            raise RuntimeError("SQLite path is not configured")
        conn = sqlite3.connect(self.path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS summary_logs (
                    run_id TEXT PRIMARY KEY,
                    scenario_id TEXT NOT NULL,
                    task TEXT NOT NULL,
                    status TEXT NOT NULL,
                    metrics TEXT NOT NULL,
                    value_summary TEXT,
                    error_type TEXT,
                    failed_summary TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_summary_logs_scenario ON summary_logs (scenario_id)")

    @staticmethod
    def _from_row(row: sqlite3.Row) -> dict[str, Any]:
        result: dict[str, Any] = {
            "run_id": row["run_id"],
            "scenario_id": row["scenario_id"],
            "task": row["task"],
            "status": row["status"],
            "metrics": json.loads(row["metrics"]),
            "created_at": row["created_at"],
        }
        if row["value_summary"] is not None:
            result["value_summary"] = row["value_summary"]
        if row["error_type"] is not None:
            result["error_type"] = row["error_type"]
        if row["failed_summary"] is not None:
            result["failed_summary"] = row["failed_summary"]
        return result
