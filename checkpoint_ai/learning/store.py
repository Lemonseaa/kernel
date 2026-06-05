"""SQLite stores for V7 blackboard objects."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from checkpoint_ai.learning.models import (
    Observation,
    ObservationSeverity,
    ObservationType,
    SafetyFinding,
    ValidationSummary,
)


class _SQLiteStore:
    """Shared SQLite helpers."""

    def __init__(self, path: str | Path) -> None:
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
        raise NotImplementedError


class ObservationStore(_SQLiteStore):
    """Persist observer blackboard facts."""

    def save(self, observation: Observation) -> str:
        """Save one observation."""

        with self._connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO observations (
                    id, business_line_id, scenario_id, observation_type, severity,
                    title, summary, source_ids, created_at, metadata
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._to_row(observation),
            )
        return observation.id

    def get(self, observation_id: str) -> Observation | None:
        """Return one observation by id."""

        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM observations WHERE id = ?", (observation_id,)).fetchone()
        return None if row is None else self._from_row(row)

    def list(
        self,
        scenario_id: str | None = None,
        business_line_id: str | None = None,
    ) -> list[Observation]:
        """List observations, scoped by scenario or business line."""

        clauses: list[str] = []
        params: list[str] = []
        if scenario_id is not None:
            clauses.append("scenario_id = ?")
            params.append(scenario_id)
        if business_line_id is not None:
            clauses.append("business_line_id = ?")
            params.append(business_line_id)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                f"SELECT * FROM observations {where} ORDER BY created_at, rowid",
                tuple(params),
            ).fetchall()
        return [self._from_row(row) for row in rows]

    def _init_schema(self) -> None:
        with self._connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS observations (
                    id TEXT PRIMARY KEY,
                    business_line_id TEXT NOT NULL,
                    scenario_id TEXT NOT NULL,
                    observation_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    title TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    source_ids TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    metadata TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_observations_scenario ON observations (scenario_id)")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_observations_business_line ON observations (business_line_id)"
            )

    @staticmethod
    def _to_row(observation: Observation) -> tuple[Any, ...]:
        return (
            observation.id,
            observation.business_line_id,
            observation.scenario_id,
            observation.observation_type.value,
            observation.severity.value,
            observation.title,
            observation.summary,
            json.dumps(observation.source_ids, ensure_ascii=False),
            observation.created_at.isoformat(),
            json.dumps(observation.metadata, ensure_ascii=False, default=str),
        )

    @staticmethod
    def _from_row(row: sqlite3.Row) -> Observation:
        return Observation(
            id=row["id"],
            business_line_id=row["business_line_id"],
            scenario_id=row["scenario_id"],
            observation_type=ObservationType(row["observation_type"]),
            severity=ObservationSeverity(row["severity"]),
            title=row["title"],
            summary=row["summary"],
            source_ids=json.loads(row["source_ids"]),
            created_at=datetime.fromisoformat(row["created_at"]).astimezone(UTC),
            metadata=json.loads(row["metadata"]),
        )


class SafetyFindingStore(_SQLiteStore):
    """Persist safety findings."""

    def save(
        self,
        finding: SafetyFinding | None = None,
        **kwargs: Any,
    ) -> str:
        """Save one finding, accepting either a model or model kwargs."""

        active = finding or SafetyFinding(**kwargs)
        with self._connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO safety_findings (
                    id, business_line_id, scenario_id, proposal_id, severity,
                    reason, source_ids, created_at, metadata
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._to_row(active),
            )
        return active.id

    def get(self, finding_id: str) -> SafetyFinding | None:
        """Return one safety finding."""

        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM safety_findings WHERE id = ?", (finding_id,)).fetchone()
        return None if row is None else self._from_row(row)

    def list(self, scenario_id: str | None = None) -> list[SafetyFinding]:
        """List safety findings."""

        where = "WHERE scenario_id = ?" if scenario_id is not None else ""
        params = (scenario_id,) if scenario_id is not None else ()
        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                f"SELECT * FROM safety_findings {where} ORDER BY created_at, rowid",
                params,
            ).fetchall()
        return [self._from_row(row) for row in rows]

    def _init_schema(self) -> None:
        with self._connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS safety_findings (
                    id TEXT PRIMARY KEY,
                    business_line_id TEXT NOT NULL,
                    scenario_id TEXT NOT NULL,
                    proposal_id TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    source_ids TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    metadata TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_safety_findings_scenario ON safety_findings (scenario_id)")

    @staticmethod
    def _to_row(finding: SafetyFinding) -> tuple[Any, ...]:
        return (
            finding.id,
            finding.business_line_id,
            finding.scenario_id,
            finding.proposal_id,
            finding.severity,
            finding.reason,
            json.dumps(finding.source_ids, ensure_ascii=False),
            finding.created_at.isoformat(),
            json.dumps(finding.metadata, ensure_ascii=False, default=str),
        )

    @staticmethod
    def _from_row(row: sqlite3.Row) -> SafetyFinding:
        return SafetyFinding(
            id=row["id"],
            business_line_id=row["business_line_id"],
            scenario_id=row["scenario_id"],
            proposal_id=row["proposal_id"],
            severity=row["severity"],
            reason=row["reason"],
            source_ids=json.loads(row["source_ids"]),
            created_at=datetime.fromisoformat(row["created_at"]).astimezone(UTC),
            metadata=json.loads(row["metadata"]),
        )


class ValidationSummaryStore(_SQLiteStore):
    """Persist validation summaries."""

    def save(
        self,
        record: ValidationSummary | None = None,
        **kwargs: Any,
    ) -> str:
        """Save one validation summary, accepting either a model or kwargs."""

        active = record or ValidationSummary(**kwargs)
        with self._connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO validation_summaries (
                    id, business_line_id, scenario_id, proposal_id, shadow_result_id,
                    improved, summary, metric_diffs, recommendation, source_ids,
                    created_at, metadata
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._to_row(active),
            )
        return active.id

    def get(self, summary_id: str) -> ValidationSummary | None:
        """Return one validation summary."""

        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM validation_summaries WHERE id = ?", (summary_id,)).fetchone()
        return None if row is None else self._from_row(row)

    def list(self, scenario_id: str | None = None) -> list[ValidationSummary]:
        """List validation summaries."""

        where = "WHERE scenario_id = ?" if scenario_id is not None else ""
        params = (scenario_id,) if scenario_id is not None else ()
        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                f"SELECT * FROM validation_summaries {where} ORDER BY created_at, rowid",
                params,
            ).fetchall()
        return [self._from_row(row) for row in rows]

    def _init_schema(self) -> None:
        with self._connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS validation_summaries (
                    id TEXT PRIMARY KEY,
                    business_line_id TEXT NOT NULL,
                    scenario_id TEXT NOT NULL,
                    proposal_id TEXT NOT NULL,
                    shadow_result_id TEXT NOT NULL,
                    improved INTEGER NOT NULL,
                    summary TEXT NOT NULL,
                    metric_diffs TEXT NOT NULL,
                    recommendation TEXT NOT NULL,
                    source_ids TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    metadata TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_validation_summaries_scenario "
                "ON validation_summaries (scenario_id)"
            )

    @staticmethod
    def _to_row(summary: ValidationSummary) -> tuple[Any, ...]:
        return (
            summary.id,
            summary.business_line_id,
            summary.scenario_id,
            summary.proposal_id,
            summary.shadow_result_id,
            1 if summary.improved else 0,
            summary.summary,
            json.dumps(summary.metric_diffs, ensure_ascii=False, default=str),
            summary.recommendation,
            json.dumps(summary.source_ids, ensure_ascii=False),
            summary.created_at.isoformat(),
            json.dumps(summary.metadata, ensure_ascii=False, default=str),
        )

    @staticmethod
    def _from_row(row: sqlite3.Row) -> ValidationSummary:
        return ValidationSummary(
            id=row["id"],
            business_line_id=row["business_line_id"],
            scenario_id=row["scenario_id"],
            proposal_id=row["proposal_id"],
            shadow_result_id=row["shadow_result_id"],
            improved=bool(row["improved"]),
            summary=row["summary"],
            metric_diffs=json.loads(row["metric_diffs"]),
            recommendation=row["recommendation"],
            source_ids=json.loads(row["source_ids"]),
            created_at=datetime.fromisoformat(row["created_at"]).astimezone(UTC),
            metadata=json.loads(row["metadata"]),
        )
