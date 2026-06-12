"""SQLite store for internal Agent configuration."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from loop_harness.agent_config.models import AgentConfig, AgentRole


class AgentConfigStore:
    """Persist AgentConfig rows."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def save(self, config: AgentConfig) -> str:
        """Create or update a config."""

        with self._connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO agent_configs (
                    id, business_line_id, role, config_version_id, skills, tools,
                    mcp_servers, triggers, constraints, model, created_at, updated_at, metadata
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._to_row(config),
            )
        return config.id

    def list(
        self,
        business_line_id: str | None = None,
        role: AgentRole | None = None,
    ) -> list[AgentConfig]:
        """List configs, optionally scoped by business line and role."""

        clauses: list[str] = []
        params: list[str] = []
        if business_line_id is not None:
            clauses.append("business_line_id = ?")
            params.append(business_line_id)
        if role is not None:
            clauses.append("role = ?")
            params.append(role.value)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                f"SELECT * FROM agent_configs {where} ORDER BY created_at, rowid",
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
                CREATE TABLE IF NOT EXISTS agent_configs (
                    id TEXT PRIMARY KEY,
                    business_line_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    config_version_id TEXT NOT NULL,
                    skills TEXT NOT NULL,
                    tools TEXT NOT NULL,
                    mcp_servers TEXT NOT NULL,
                    triggers TEXT NOT NULL,
                    constraints TEXT NOT NULL,
                    model TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_configs_bl ON agent_configs (business_line_id)")

    @staticmethod
    def _to_row(config: AgentConfig) -> tuple[Any, ...]:
        return (
            config.id,
            config.business_line_id,
            config.role.value,
            config.config_version_id,
            json.dumps(config.skills, ensure_ascii=False),
            json.dumps(config.tools, ensure_ascii=False),
            json.dumps(config.mcp_servers, ensure_ascii=False),
            json.dumps(config.triggers, ensure_ascii=False),
            json.dumps(config.constraints, ensure_ascii=False),
            config.model,
            config.created_at.isoformat(),
            config.updated_at.isoformat(),
            json.dumps(config.metadata, ensure_ascii=False, default=str),
        )

    @staticmethod
    def _from_row(row: sqlite3.Row) -> AgentConfig:
        return AgentConfig(
            id=row["id"],
            business_line_id=row["business_line_id"],
            role=AgentRole(row["role"]),
            config_version_id=row["config_version_id"],
            skills=json.loads(row["skills"]),
            tools=json.loads(row["tools"]),
            mcp_servers=json.loads(row["mcp_servers"]),
            triggers=json.loads(row["triggers"]),
            constraints=json.loads(row["constraints"]),
            model=row["model"],
            created_at=datetime.fromisoformat(row["created_at"]).astimezone(UTC),
            updated_at=datetime.fromisoformat(row["updated_at"]).astimezone(UTC),
            metadata=json.loads(row["metadata"]),
        )
