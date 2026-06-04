"""SQLite storage for shadow results."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from checkpoint_ai.shadow.models import ShadowResult


class ShadowResultStore:
    """Persist shadow results and baseline comparisons."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def save(self, result: ShadowResult) -> str:
        """Save one shadow result."""

        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO shadow_results (
                    id, proposal_id, scenario_id, agent_id, run_id, is_shadow,
                    status, passed, answer, value_summary, baseline_metrics,
                    shadow_metrics, metric_diff, error_type, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    proposal_id=excluded.proposal_id,
                    scenario_id=excluded.scenario_id,
                    agent_id=excluded.agent_id,
                    run_id=excluded.run_id,
                    is_shadow=excluded.is_shadow,
                    status=excluded.status,
                    passed=excluded.passed,
                    answer=excluded.answer,
                    value_summary=excluded.value_summary,
                    baseline_metrics=excluded.baseline_metrics,
                    shadow_metrics=excluded.shadow_metrics,
                    metric_diff=excluded.metric_diff,
                    error_type=excluded.error_type,
                    created_at=excluded.created_at
                """,
                self._to_row(result),
            )
        return result.id

    def get(self, result_id: str) -> ShadowResult | None:
        """Return one shadow result by id."""

        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM shadow_results WHERE id = ?", (result_id,)).fetchone()
        return None if row is None else self._from_row(row)

    def query_by_proposal(self, proposal_id: str) -> list[ShadowResult]:
        """Return shadow results for one proposal."""

        return self._query("proposal_id = ?", proposal_id)

    def query_by_scenario(self, scenario_id: str) -> list[ShadowResult]:
        """Return shadow results for one scenario."""

        return self._query("scenario_id = ?", scenario_id)

    def _query(self, clause: str, value: str) -> list[ShadowResult]:
        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                f"SELECT * FROM shadow_results WHERE {clause} ORDER BY created_at, rowid",
                (value,),
            ).fetchall()
        return [self._from_row(row) for row in rows]

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
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
                CREATE TABLE IF NOT EXISTS shadow_results (
                    id TEXT PRIMARY KEY,
                    proposal_id TEXT NOT NULL,
                    scenario_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    is_shadow INTEGER NOT NULL,
                    status TEXT NOT NULL,
                    passed INTEGER NOT NULL,
                    answer TEXT NOT NULL,
                    value_summary TEXT NOT NULL,
                    baseline_metrics TEXT NOT NULL,
                    shadow_metrics TEXT NOT NULL,
                    metric_diff TEXT NOT NULL,
                    error_type TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_shadow_results_proposal "
                "ON shadow_results (proposal_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_shadow_results_scenario "
                "ON shadow_results (scenario_id)"
            )

    @staticmethod
    def _to_row(result: ShadowResult) -> tuple[Any, ...]:
        return (
            result.id,
            result.proposal_id,
            result.scenario_id,
            result.agent_id,
            result.run_id,
            1 if result.is_shadow else 0,
            result.status,
            1 if result.passed else 0,
            result.answer,
            result.value_summary,
            json.dumps(result.baseline_metrics, ensure_ascii=False, default=str),
            json.dumps(result.shadow_metrics, ensure_ascii=False, default=str),
            json.dumps(result.metric_diff, ensure_ascii=False, default=str),
            result.error_type,
            result.created_at.isoformat(),
        )

    @staticmethod
    def _from_row(row: sqlite3.Row) -> ShadowResult:
        return ShadowResult(
            id=row["id"],
            proposal_id=row["proposal_id"],
            scenario_id=row["scenario_id"],
            agent_id=row["agent_id"],
            run_id=row["run_id"],
            is_shadow=bool(row["is_shadow"]),
            status=row["status"],
            passed=bool(row["passed"]),
            answer=row["answer"],
            value_summary=row["value_summary"],
            baseline_metrics=json.loads(row["baseline_metrics"]),
            shadow_metrics=json.loads(row["shadow_metrics"]),
            metric_diff=json.loads(row["metric_diff"]),
            error_type=row["error_type"],
            created_at=datetime.fromisoformat(row["created_at"]).astimezone(UTC),
        )
