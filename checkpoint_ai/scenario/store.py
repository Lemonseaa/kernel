"""SQLite persistence for V2 scenarios."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from checkpoint_ai.scenario.models import Scenario


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
                INSERT INTO scenarios (id, name, description, adapter_type, adapter_config, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,
                    description=excluded.description,
                    adapter_type=excluded.adapter_type,
                    adapter_config=excluded.adapter_config
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

    def list(self) -> list[Scenario]:
        """List scenarios in creation order."""

        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM scenarios ORDER BY created_at, rowid").fetchall()
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
                CREATE TABLE IF NOT EXISTS scenarios (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT NOT NULL,
                    adapter_type TEXT NOT NULL,
                    adapter_config TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_scenarios_adapter ON scenarios (adapter_type)")

    @staticmethod
    def _to_row(scenario: Scenario) -> tuple[Any, ...]:
        return (
            scenario.id,
            scenario.name,
            scenario.description,
            scenario.adapter_type,
            json.dumps(scenario.adapter_config, ensure_ascii=False, default=str),
            scenario.created_at.isoformat(),
        )

    @staticmethod
    def _from_row(row: sqlite3.Row) -> Scenario:
        return Scenario(
            id=row["id"],
            name=row["name"],
            description=row["description"],
            adapter_type=row["adapter_type"],
            adapter_config=json.loads(row["adapter_config"]),
            created_at=datetime.fromisoformat(row["created_at"]).astimezone(UTC),
        )
