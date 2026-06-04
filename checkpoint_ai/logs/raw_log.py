"""Raw run log storage for V2.1 scenarios."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from checkpoint_ai.adapter import AgentRunRequest, AgentRunResult


class RawLogStore:
    """Persist complete request and result payloads."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path is not None else None
        self._memory: dict[str, dict[str, Any]] = {}
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._init_schema()

    def save(self, run_id: str, request: AgentRunRequest, result: AgentRunResult) -> None:
        """Save the raw input and output for one run."""

        row = {
            "run_id": run_id,
            "scenario_id": request.scenario_id,
            "request": request.model_dump(mode="json"),
            "result": result.model_dump(mode="json"),
            "created_at": datetime.now(UTC).isoformat(),
        }
        if self.path is None:
            self._memory[run_id] = row
            return
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO raw_logs (run_id, scenario_id, request, result, created_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(run_id) DO UPDATE SET
                    scenario_id=excluded.scenario_id,
                    request=excluded.request,
                    result=excluded.result,
                    created_at=excluded.created_at
                """,
                (
                    row["run_id"],
                    row["scenario_id"],
                    json.dumps(row["request"], ensure_ascii=False, default=str),
                    json.dumps(row["result"], ensure_ascii=False, default=str),
                    row["created_at"],
                ),
            )

    def get(self, run_id: str) -> dict[str, Any] | None:
        """Return one raw log by run id."""

        if self.path is None:
            return self._memory.get(run_id)
        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM raw_logs WHERE run_id = ?", (run_id,)).fetchone()
        return None if row is None else self._from_row(row)

    def query_by_scenario(self, scenario_id: str) -> list[dict[str, Any]]:
        """Return raw logs for one scenario."""

        if self.path is None:
            return [row for row in self._memory.values() if row["scenario_id"] == scenario_id]
        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM raw_logs WHERE scenario_id = ? ORDER BY created_at, rowid",
                (scenario_id,),
            ).fetchall()
        return [self._from_row(row) for row in rows]

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
                CREATE TABLE IF NOT EXISTS raw_logs (
                    run_id TEXT PRIMARY KEY,
                    scenario_id TEXT NOT NULL,
                    request TEXT NOT NULL,
                    result TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_raw_logs_scenario ON raw_logs (scenario_id)")

    @staticmethod
    def _from_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "run_id": row["run_id"],
            "scenario_id": row["scenario_id"],
            "request": json.loads(row["request"]),
            "result": json.loads(row["result"]),
            "created_at": row["created_at"],
        }
