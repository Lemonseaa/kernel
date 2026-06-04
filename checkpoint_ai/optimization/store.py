"""SQLite storage for parameter suggestions."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from checkpoint_ai.optimization.models import (
    OptimizationDirection,
    ParameterSuggestion,
    ParameterSuggestionStatus,
)


class ParameterSuggestionStore:
    """Persist continuous-parameter suggestions."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def save(self, suggestion: ParameterSuggestion) -> str:
        """Create or update a suggestion."""

        suggestion.updated_at = datetime.now(UTC)
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO parameter_suggestions (
                    id, scenario_id, target_id, parameter_name, suggested_value,
                    expected_score, confidence, reason, observations_used,
                    direction, status, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    scenario_id=excluded.scenario_id,
                    target_id=excluded.target_id,
                    parameter_name=excluded.parameter_name,
                    suggested_value=excluded.suggested_value,
                    expected_score=excluded.expected_score,
                    confidence=excluded.confidence,
                    reason=excluded.reason,
                    observations_used=excluded.observations_used,
                    direction=excluded.direction,
                    status=excluded.status,
                    updated_at=excluded.updated_at
                """,
                self._to_row(suggestion),
            )
        return suggestion.id

    def get(self, suggestion_id: str) -> ParameterSuggestion | None:
        """Return one suggestion by id."""

        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM parameter_suggestions WHERE id = ?",
                (suggestion_id,),
            ).fetchone()
        return None if row is None else self._from_row(row)

    def list(
        self,
        scenario_id: str | None = None,
        status: ParameterSuggestionStatus | None = None,
    ) -> list[ParameterSuggestion]:
        """List suggestions."""

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
                f"SELECT * FROM parameter_suggestions {where} ORDER BY created_at, rowid",
                tuple(params),
            ).fetchall()
        return [self._from_row(row) for row in rows]

    def update_status(
        self,
        suggestion_id: str,
        status: ParameterSuggestionStatus,
    ) -> bool:
        """Update suggestion workflow status."""

        suggestion = self.get(suggestion_id)
        if suggestion is None:
            return False
        suggestion.status = status
        self.save(suggestion)
        return True

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
                CREATE TABLE IF NOT EXISTS parameter_suggestions (
                    id TEXT PRIMARY KEY,
                    scenario_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    parameter_name TEXT NOT NULL,
                    suggested_value REAL NOT NULL,
                    expected_score REAL NOT NULL,
                    confidence REAL NOT NULL,
                    reason TEXT NOT NULL,
                    observations_used INTEGER NOT NULL,
                    direction TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_parameter_suggestions_scenario "
                "ON parameter_suggestions (scenario_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_parameter_suggestions_status "
                "ON parameter_suggestions (status)"
            )

    @staticmethod
    def _to_row(suggestion: ParameterSuggestion) -> tuple[Any, ...]:
        return (
            suggestion.id,
            suggestion.scenario_id,
            suggestion.target_id,
            suggestion.parameter_name,
            suggestion.suggested_value,
            suggestion.expected_score,
            suggestion.confidence,
            suggestion.reason,
            suggestion.observations_used,
            suggestion.direction.value,
            suggestion.status.value,
            suggestion.created_at.isoformat(),
            suggestion.updated_at.isoformat(),
        )

    @staticmethod
    def _from_row(row: sqlite3.Row) -> ParameterSuggestion:
        return ParameterSuggestion(
            id=row["id"],
            scenario_id=row["scenario_id"],
            target_id=row["target_id"],
            parameter_name=row["parameter_name"],
            suggested_value=row["suggested_value"],
            expected_score=row["expected_score"],
            confidence=row["confidence"],
            reason=row["reason"],
            observations_used=row["observations_used"],
            direction=OptimizationDirection(row["direction"]),
            status=ParameterSuggestionStatus(row["status"]),
            created_at=datetime.fromisoformat(row["created_at"]).astimezone(UTC),
            updated_at=datetime.fromisoformat(row["updated_at"]).astimezone(UTC),
        )
