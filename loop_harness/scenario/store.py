"""SQLite persistence for V2 scenarios."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from loop_harness.scenario.models import Scenario, ScenarioStatus


class ScenarioStore:
    """Persist scenarios so CLI commands can share state."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def save(self, scenario: Scenario) -> str:
        """Create or replace one scenario."""

        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO scenarios (
                    id, name, description, adapter_type, business_line_id, adapter_config,
                    status, metadata, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,
                    description=excluded.description,
                    adapter_type=excluded.adapter_type,
                    business_line_id=excluded.business_line_id,
                    adapter_config=excluded.adapter_config,
                    status=excluded.status,
                    metadata=excluded.metadata
                """,
                self._to_row(scenario),
            )
        return scenario.id

    def get(self, scenario_id: str) -> Scenario | None:
        """Return one scenario by id."""

        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM scenarios WHERE id = ?", (scenario_id,)).fetchone()
        return None if row is None else self._from_row(row)

    def list(self, business_line_id: str | None = None) -> list[Scenario]:
        """List scenarios in creation order."""

        where = "WHERE business_line_id = ?" if business_line_id is not None else ""
        params = (business_line_id,) if business_line_id is not None else ()
        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                f"SELECT * FROM scenarios {where} ORDER BY created_at, rowid",
                params,
            ).fetchall()
        return [self._from_row(row) for row in rows]

    def archive(self, scenario_id: str, reason: str) -> bool:
        """Archive one scenario without deleting historical data."""

        scenario = self.get(scenario_id)
        if scenario is None:
            return False
        scenario.status = ScenarioStatus.ARCHIVED
        scenario.metadata = {**scenario.metadata, "archive_reason": reason}
        self.save(scenario)
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
                CREATE TABLE IF NOT EXISTS scenarios (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    adapter_type TEXT NOT NULL,
                    business_line_id TEXT,
                    adapter_config TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    metadata TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL
                )
                """
            )
            self._ensure_columns(conn)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_scenarios_adapter ON scenarios (adapter_type)")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_scenarios_business_line "
                "ON scenarios (business_line_id)"
            )

    @staticmethod
    def _ensure_columns(conn: sqlite3.Connection) -> None:
        existing = {row[1] for row in conn.execute("PRAGMA table_info(scenarios)").fetchall()}
        if "business_line_id" not in existing:
            conn.execute("ALTER TABLE scenarios ADD COLUMN business_line_id TEXT")
        if "status" not in existing:
            conn.execute("ALTER TABLE scenarios ADD COLUMN status TEXT NOT NULL DEFAULT 'active'")
        if "metadata" not in existing:
            conn.execute("ALTER TABLE scenarios ADD COLUMN metadata TEXT NOT NULL DEFAULT '{}'")

    @staticmethod
    def _to_row(scenario: Scenario) -> tuple[Any, ...]:
        return (
            scenario.id,
            scenario.name,
            scenario.description,
            scenario.adapter_type,
            scenario.business_line_id,
            json.dumps(scenario.adapter_config, ensure_ascii=False, default=str),
            scenario.status.value,
            json.dumps(scenario.metadata, ensure_ascii=False, default=str),
            scenario.created_at.isoformat(),
        )

    @staticmethod
    def _from_row(row: sqlite3.Row) -> Scenario:
        return Scenario(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            adapter_type=row["adapter_type"],
            business_line_id=row["business_line_id"],
            adapter_config=json.loads(row["adapter_config"]),
            status=ScenarioStatus(row["status"]),
            metadata=json.loads(row["metadata"]),
            created_at=datetime.fromisoformat(row["created_at"]).astimezone(UTC),
        )
