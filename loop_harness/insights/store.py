"""SQLite storage for cross-scenario insights."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from loop_harness.insights.cross_scenario import (
    CrossScenarioInsight,
    CrossScenarioInsightDecision,
)


class CrossScenarioInsightStore:
    """Persist cross-scenario insight previews."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def save(self, insight: CrossScenarioInsight) -> str:
        """Save one insight."""

        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO cross_scenario_insights (
                    id, source_scenario_id, target_scenario_id, decision,
                    similarity_score, reason, risk, source_evidence_ids,
                    rejection_reasons, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    decision=excluded.decision,
                    similarity_score=excluded.similarity_score,
                    reason=excluded.reason,
                    risk=excluded.risk,
                    source_evidence_ids=excluded.source_evidence_ids,
                    rejection_reasons=excluded.rejection_reasons
                """,
                self._to_row(insight),
            )
        return insight.id

    def get(self, insight_id: str) -> CrossScenarioInsight | None:
        """Return one insight."""

        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM cross_scenario_insights WHERE id = ?",
                (insight_id,),
            ).fetchone()
        return None if row is None else self._from_row(row)

    def list(self) -> list[CrossScenarioInsight]:
        """List insights."""

        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM cross_scenario_insights ORDER BY created_at, rowid"
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
                CREATE TABLE IF NOT EXISTS cross_scenario_insights (
                    id TEXT PRIMARY KEY,
                    source_scenario_id TEXT NOT NULL,
                    target_scenario_id TEXT NOT NULL,
                    decision TEXT NOT NULL,
                    similarity_score REAL NOT NULL,
                    reason TEXT NOT NULL,
                    risk TEXT NOT NULL,
                    source_evidence_ids TEXT NOT NULL,
                    rejection_reasons TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    @staticmethod
    def _to_row(insight: CrossScenarioInsight) -> tuple[Any, ...]:
        return (
            insight.id,
            insight.source_scenario_id,
            insight.target_scenario_id,
            insight.decision.value,
            insight.similarity_score,
            insight.reason,
            insight.risk,
            json.dumps(insight.source_evidence_ids, ensure_ascii=False),
            json.dumps(insight.rejection_reasons, ensure_ascii=False),
            insight.created_at.isoformat(),
        )

    @staticmethod
    def _from_row(row: sqlite3.Row) -> CrossScenarioInsight:
        return CrossScenarioInsight(
            id=row["id"],
            source_scenario_id=row["source_scenario_id"],
            target_scenario_id=row["target_scenario_id"],
            decision=CrossScenarioInsightDecision(row["decision"]),
            similarity_score=row["similarity_score"],
            reason=row["reason"],
            risk=row["risk"],
            source_evidence_ids=json.loads(row["source_evidence_ids"]),
            rejection_reasons=json.loads(row["rejection_reasons"]),
            created_at=datetime.fromisoformat(row["created_at"]).astimezone(UTC),
        )
