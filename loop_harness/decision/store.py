"""SQLite storage for decision audit records."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from loop_harness.decision.models import DecisionKind, DecisionRecord


class DecisionLogStore:
    """Persist auditable operator and system decisions."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def record(self, record: DecisionRecord) -> str:
        """Create one decision record."""

        with self._connection() as conn:
            conn.execute(
                """
                INSERT OR IGNORE INTO decision_log (
                    id, source_id, source_type, kind, scenario_id, actor, action,
                    comment, before, after, result, details, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._to_row(record),
            )
        return record.id

    def get(self, record_id: str) -> DecisionRecord | None:
        """Return one decision record by id."""

        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM decision_log WHERE id = ?", (record_id,)).fetchone()
        return None if row is None else self._from_row(row)

    def list(
        self,
        source_id: str | None = None,
        scenario_id: str | None = None,
    ) -> list[DecisionRecord]:
        """List decision records, optionally filtered by source or scenario."""

        clauses: list[str] = []
        params: list[str] = []
        if source_id is not None:
            clauses.append("source_id = ?")
            params.append(source_id)
        if scenario_id is not None:
            clauses.append("scenario_id = ?")
            params.append(scenario_id)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                f"SELECT * FROM decision_log {where} ORDER BY created_at, rowid",
                tuple(params),
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
                CREATE TABLE IF NOT EXISTS decision_log (
                    id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    source_type TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    scenario_id TEXT,
                    actor TEXT NOT NULL,
                    action TEXT NOT NULL,
                    comment TEXT NOT NULL,
                    before TEXT NOT NULL,
                    after TEXT NOT NULL,
                    result TEXT NOT NULL,
                    details TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_decision_log_source "
                "ON decision_log (source_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_decision_log_scenario "
                "ON decision_log (scenario_id)"
            )

    @staticmethod
    def _to_row(record: DecisionRecord) -> tuple[Any, ...]:
        return (
            record.id,
            record.source_id,
            record.source_type,
            record.kind.value,
            record.scenario_id,
            record.actor,
            record.action,
            record.comment,
            json.dumps(record.before, ensure_ascii=False, default=str),
            json.dumps(record.after, ensure_ascii=False, default=str),
            json.dumps(record.result, ensure_ascii=False, default=str),
            json.dumps(record.details, ensure_ascii=False, default=str),
            record.created_at.isoformat(),
        )

    @staticmethod
    def _from_row(row: sqlite3.Row) -> DecisionRecord:
        return DecisionRecord(
            id=row["id"],
            source_id=row["source_id"],
            source_type=row["source_type"],
            kind=DecisionKind(row["kind"]),
            scenario_id=row["scenario_id"],
            actor=row["actor"],
            action=row["action"],
            comment=row["comment"],
            before=json.loads(row["before"]),
            after=json.loads(row["after"]),
            result=json.loads(row["result"]),
            details=json.loads(row["details"]),
            created_at=datetime.fromisoformat(row["created_at"]).astimezone(UTC),
        )
