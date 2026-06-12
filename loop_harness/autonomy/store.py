"""SQLite storage for autonomous action records."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from loop_harness.autonomy.models import AutonomyActionLog, AutonomyActionStatus


class AutonomyActionStore:
    """Persist low-risk autonomous action records."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def create(
        self,
        scenario_id: str,
        proposal_id: str,
        action_type: str,
        checkpoint_id: str,
        reason: str,
    ) -> AutonomyActionLog:
        """Create one pending action and require a checkpoint id."""

        action = AutonomyActionLog(
            scenario_id=scenario_id,
            proposal_id=proposal_id,
            action_type=action_type,
            checkpoint_id=checkpoint_id,
            reason=reason,
        )
        self.save(action)
        return action

    def save(self, action: AutonomyActionLog) -> str:
        """Create or update one action record."""

        action.updated_at = datetime.now(UTC)
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO autonomy_actions (
                    id, scenario_id, proposal_id, action_type, checkpoint_id,
                    reason, status, result, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    scenario_id=excluded.scenario_id,
                    proposal_id=excluded.proposal_id,
                    action_type=excluded.action_type,
                    checkpoint_id=excluded.checkpoint_id,
                    reason=excluded.reason,
                    status=excluded.status,
                    result=excluded.result,
                    updated_at=excluded.updated_at
                """,
                self._to_row(action),
            )
        return action.id

    def get(self, action_id: str) -> AutonomyActionLog | None:
        """Return one action by id."""

        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM autonomy_actions WHERE id = ?", (action_id,)).fetchone()
        return None if row is None else self._from_row(row)

    def list(
        self,
        scenario_id: str | None = None,
        status: AutonomyActionStatus | None = None,
    ) -> list[AutonomyActionLog]:
        """List actions, optionally filtered by scenario or status."""

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
                f"SELECT * FROM autonomy_actions {where} ORDER BY created_at, rowid",
                tuple(params),
            ).fetchall()
        return [self._from_row(row) for row in rows]

    def update_status(
        self,
        action_id: str,
        status: AutonomyActionStatus,
        result: dict[str, Any] | None = None,
    ) -> bool:
        """Update one action lifecycle state."""

        action = self.get(action_id)
        if action is None:
            return False
        action.status = status
        if result is not None:
            action.result = result
        self.save(action)
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
                CREATE TABLE IF NOT EXISTS autonomy_actions (
                    id TEXT PRIMARY KEY,
                    scenario_id TEXT NOT NULL,
                    proposal_id TEXT NOT NULL,
                    action_type TEXT NOT NULL,
                    checkpoint_id TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    status TEXT NOT NULL,
                    result TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_autonomy_actions_scenario "
                "ON autonomy_actions (scenario_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_autonomy_actions_status "
                "ON autonomy_actions (status)"
            )

    @staticmethod
    def _to_row(action: AutonomyActionLog) -> tuple[Any, ...]:
        return (
            action.id,
            action.scenario_id,
            action.proposal_id,
            action.action_type,
            action.checkpoint_id,
            action.reason,
            action.status.value,
            json.dumps(action.result, ensure_ascii=False, default=str),
            action.created_at.isoformat(),
            action.updated_at.isoformat(),
        )

    @staticmethod
    def _from_row(row: sqlite3.Row) -> AutonomyActionLog:
        return AutonomyActionLog(
            id=row["id"],
            scenario_id=row["scenario_id"],
            proposal_id=row["proposal_id"],
            action_type=row["action_type"],
            checkpoint_id=row["checkpoint_id"],
            reason=row["reason"],
            status=AutonomyActionStatus(row["status"]),
            result=json.loads(row["result"]),
            created_at=datetime.fromisoformat(row["created_at"]).astimezone(UTC),
            updated_at=datetime.fromisoformat(row["updated_at"]).astimezone(UTC),
        )


class AutonomyQueueStateStore:
    """Persist operator queue pause state across API requests."""

    _QUEUE_ID = "default"

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def is_paused(self) -> bool:
        """Return whether the autonomy queue is paused."""

        with self._connection() as conn:
            row = conn.execute(
                "SELECT paused FROM autonomy_queue_state WHERE id = ?",
                (self._QUEUE_ID,),
            ).fetchone()
        return bool(row[0]) if row is not None else False

    def pause(self) -> None:
        """Persist paused queue state."""

        self._set_paused(True)

    def resume(self) -> None:
        """Persist running queue state."""

        self._set_paused(False)

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _set_paused(self, paused: bool) -> None:
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO autonomy_queue_state (id, paused, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    paused=excluded.paused,
                    updated_at=excluded.updated_at
                """,
                (self._QUEUE_ID, int(paused), datetime.now(UTC).isoformat()),
            )

    def _init_schema(self) -> None:
        with self._connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS autonomy_queue_state (
                    id TEXT PRIMARY KEY,
                    paused INTEGER NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
