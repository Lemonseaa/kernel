"""SQLite storage for version recommendations."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from loop_harness.recommendation.models import (
    RecommendationDecision,
    RecommendationStatus,
    VersionRecommendation,
)


class VersionRecommendationStore:
    """Persist evidence-based version recommendations."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def save(self, recommendation: VersionRecommendation) -> str:
        """Create or update a recommendation."""

        recommendation.updated_at = datetime.now(UTC)
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO version_recommendations (
                    id, scenario_id, target_id, proposal_id, decision, status,
                    confidence, objective_score, reason, recommended_action,
                    source_shadow_ids, evidence, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    scenario_id=excluded.scenario_id,
                    target_id=excluded.target_id,
                    proposal_id=excluded.proposal_id,
                    decision=excluded.decision,
                    status=excluded.status,
                    confidence=excluded.confidence,
                    objective_score=excluded.objective_score,
                    reason=excluded.reason,
                    recommended_action=excluded.recommended_action,
                    source_shadow_ids=excluded.source_shadow_ids,
                    evidence=excluded.evidence,
                    updated_at=excluded.updated_at
                """,
                self._to_row(recommendation),
            )
        return recommendation.id

    def get(self, recommendation_id: str) -> VersionRecommendation | None:
        """Return one recommendation by id."""

        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM version_recommendations WHERE id = ?",
                (recommendation_id,),
            ).fetchone()
        return None if row is None else self._from_row(row)

    def list(
        self,
        scenario_id: str | None = None,
        status: RecommendationStatus | None = None,
    ) -> list[VersionRecommendation]:
        """List recommendations."""

        clauses: list[str] = []
        params: list[str] = []
        if scenario_id is not None:
            clauses.append("scenario_id = ?")
            params.append(scenario_id)
        if status is not None:
            clauses.append("status = ?")
            params.append(status.value)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                f"SELECT * FROM version_recommendations {where} ORDER BY created_at, rowid",
                tuple(params),
            ).fetchall()
        return [self._from_row(row) for row in rows]

    def update_status(
        self,
        recommendation_id: str,
        status: RecommendationStatus,
    ) -> bool:
        """Update recommendation workflow status."""

        recommendation = self.get(recommendation_id)
        if recommendation is None:
            return False
        recommendation.status = status
        return bool(self.save(recommendation))

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
                CREATE TABLE IF NOT EXISTS version_recommendations (
                    id TEXT PRIMARY KEY,
                    scenario_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    proposal_id TEXT,
                    decision TEXT NOT NULL,
                    status TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    objective_score REAL NOT NULL,
                    reason TEXT NOT NULL,
                    recommended_action TEXT NOT NULL,
                    source_shadow_ids TEXT NOT NULL,
                    evidence TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_version_recommendations_scenario "
                "ON version_recommendations (scenario_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_version_recommendations_status "
                "ON version_recommendations (status)"
            )

    @staticmethod
    def _to_row(recommendation: VersionRecommendation) -> tuple[Any, ...]:
        return (
            recommendation.id,
            recommendation.scenario_id,
            recommendation.target_id,
            recommendation.proposal_id,
            recommendation.decision.value,
            recommendation.status.value,
            recommendation.confidence,
            recommendation.objective_score,
            recommendation.reason,
            recommendation.recommended_action,
            json.dumps(recommendation.source_shadow_ids, ensure_ascii=False),
            json.dumps(recommendation.evidence, ensure_ascii=False, default=str),
            recommendation.created_at.isoformat(),
            recommendation.updated_at.isoformat(),
        )

    @staticmethod
    def _from_row(row: sqlite3.Row) -> VersionRecommendation:
        return VersionRecommendation(
            id=row["id"],
            scenario_id=row["scenario_id"],
            target_id=row["target_id"],
            proposal_id=row["proposal_id"],
            decision=RecommendationDecision(row["decision"]),
            status=RecommendationStatus(row["status"]),
            confidence=row["confidence"],
            objective_score=row["objective_score"],
            reason=row["reason"],
            recommended_action=row["recommended_action"],
            source_shadow_ids=json.loads(row["source_shadow_ids"]),
            evidence=json.loads(row["evidence"]),
            created_at=datetime.fromisoformat(row["created_at"]).astimezone(UTC),
            updated_at=datetime.fromisoformat(row["updated_at"]).astimezone(UTC),
        )
