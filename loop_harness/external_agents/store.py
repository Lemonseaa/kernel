"""SQLite store for external Agent connections."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from loop_harness.adapter import AdapterCapabilities
from loop_harness.external_agents.models import ExternalAgentConnection


class ExternalAgentConnectionStore:
    """Persist external adapter connection metadata."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def save(self, connection: ExternalAgentConnection) -> str:
        """Create or update a connection."""

        with self._connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO external_agent_connections (
                    id, business_line_id, scenario_id, name, adapter_type, config,
                    capabilities, active, created_at, metadata
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._to_row(connection),
            )
        return connection.id

    def list(self, business_line_id: str | None = None) -> list[ExternalAgentConnection]:
        """List external connections."""

        where = "WHERE business_line_id = ?" if business_line_id is not None else ""
        params = (business_line_id,) if business_line_id is not None else ()
        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                f"SELECT * FROM external_agent_connections {where} ORDER BY created_at, rowid",
                params,
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
                CREATE TABLE IF NOT EXISTS external_agent_connections (
                    id TEXT PRIMARY KEY,
                    business_line_id TEXT NOT NULL,
                    scenario_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    adapter_type TEXT NOT NULL,
                    config TEXT NOT NULL,
                    capabilities TEXT NOT NULL,
                    active INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    metadata TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_external_agent_connections_bl "
                "ON external_agent_connections (business_line_id)"
            )

    @staticmethod
    def _to_row(connection: ExternalAgentConnection) -> tuple[Any, ...]:
        return (
            connection.id,
            connection.business_line_id,
            connection.scenario_id,
            connection.name,
            connection.adapter_type,
            json.dumps(connection.config, ensure_ascii=False, default=str),
            json.dumps(connection.capabilities.model_dump(mode="json"), ensure_ascii=False),
            1 if connection.active else 0,
            connection.created_at.isoformat(),
            json.dumps(connection.metadata, ensure_ascii=False, default=str),
        )

    @staticmethod
    def _from_row(row: sqlite3.Row) -> ExternalAgentConnection:
        return ExternalAgentConnection(
            id=row["id"],
            business_line_id=row["business_line_id"],
            scenario_id=row["scenario_id"],
            name=row["name"],
            adapter_type=row["adapter_type"],
            config=json.loads(row["config"]),
            capabilities=AdapterCapabilities(**json.loads(row["capabilities"])),
            active=bool(row["active"]),
            created_at=datetime.fromisoformat(row["created_at"]).astimezone(UTC),
            metadata=json.loads(row["metadata"]),
        )
