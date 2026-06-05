"""SQLite storage for configuration versions and branches."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from checkpoint_ai.config_version.models import ConfigBranch, ConfigVersion


class _Store:
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


class ConfigVersionStore(_Store):
    """Persist config versions."""

    def save(self, version: ConfigVersion) -> str:
        """Create or update a config version unless it is locked."""

        existing = self.get(version.id)
        if existing is not None and existing.locked:
            raise ValueError(f"Locked config version is immutable: {version.id}")
        with self._connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO config_versions (
                    id, business_line_id, scenario_id, config, reason,
                    parent_version_id, locked, locked_reason, created_at, updated_at, metadata
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._to_row(version),
            )
        return version.id

    def get(self, version_id: str) -> ConfigVersion | None:
        """Return one version."""

        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM config_versions WHERE id = ?", (version_id,)).fetchone()
        return None if row is None else self._from_row(row)

    def list(self, scenario_id: str | None = None) -> list[ConfigVersion]:
        """List versions."""

        where = "WHERE scenario_id = ?" if scenario_id is not None else ""
        params = (scenario_id,) if scenario_id is not None else ()
        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                f"SELECT * FROM config_versions {where} ORDER BY created_at, rowid",
                params,
            ).fetchall()
        return [self._from_row(row) for row in rows]

    def _init_schema(self) -> None:
        with self._connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS config_versions (
                    id TEXT PRIMARY KEY,
                    business_line_id TEXT NOT NULL,
                    scenario_id TEXT NOT NULL,
                    config TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    parent_version_id TEXT,
                    locked INTEGER NOT NULL,
                    locked_reason TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_config_versions_scenario ON config_versions (scenario_id)")

    @staticmethod
    def _to_row(version: ConfigVersion) -> tuple[Any, ...]:
        return (
            version.id,
            version.business_line_id,
            version.scenario_id,
            json.dumps(version.config, ensure_ascii=False, default=str),
            version.reason,
            version.parent_version_id,
            1 if version.locked else 0,
            version.locked_reason,
            version.created_at.isoformat(),
            version.updated_at.isoformat(),
            json.dumps(version.metadata, ensure_ascii=False, default=str),
        )

    @staticmethod
    def _from_row(row: sqlite3.Row) -> ConfigVersion:
        return ConfigVersion(
            id=row["id"],
            business_line_id=row["business_line_id"],
            scenario_id=row["scenario_id"],
            config=json.loads(row["config"]),
            reason=row["reason"],
            parent_version_id=row["parent_version_id"],
            locked=bool(row["locked"]),
            locked_reason=row["locked_reason"],
            created_at=datetime.fromisoformat(row["created_at"]).astimezone(UTC),
            updated_at=datetime.fromisoformat(row["updated_at"]).astimezone(UTC),
            metadata=json.loads(row["metadata"]),
        )


class ConfigBranchStore(_Store):
    """Persist active optimization branches."""

    def save(self, branch: ConfigBranch) -> str:
        """Create or update a branch."""

        if branch.active:
            self.deactivate_for_scenario(branch.scenario_id)
        with self._connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO config_branches (
                    id, business_line_id, scenario_id, name, base_version_id,
                    active, created_at, metadata
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._to_row(branch),
            )
        return branch.id

    def get(self, branch_id: str) -> ConfigBranch | None:
        """Return one branch."""

        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM config_branches WHERE id = ?", (branch_id,)).fetchone()
        return None if row is None else self._from_row(row)

    def get_active(self, scenario_id: str) -> ConfigBranch | None:
        """Return active branch for one scenario."""

        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM config_branches WHERE scenario_id = ? AND active = 1 ORDER BY created_at DESC LIMIT 1",
                (scenario_id,),
            ).fetchone()
        return None if row is None else self._from_row(row)

    def deactivate_for_scenario(self, scenario_id: str) -> None:
        """Deactivate all branches for one scenario."""

        with self._connection() as conn:
            conn.execute("UPDATE config_branches SET active = 0 WHERE scenario_id = ?", (scenario_id,))

    def _init_schema(self) -> None:
        with self._connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS config_branches (
                    id TEXT PRIMARY KEY,
                    business_line_id TEXT NOT NULL,
                    scenario_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    base_version_id TEXT NOT NULL,
                    active INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    metadata TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_config_branches_scenario ON config_branches (scenario_id)")

    @staticmethod
    def _to_row(branch: ConfigBranch) -> tuple[Any, ...]:
        return (
            branch.id,
            branch.business_line_id,
            branch.scenario_id,
            branch.name,
            branch.base_version_id,
            1 if branch.active else 0,
            branch.created_at.isoformat(),
            json.dumps(branch.metadata, ensure_ascii=False, default=str),
        )

    @staticmethod
    def _from_row(row: sqlite3.Row) -> ConfigBranch:
        return ConfigBranch(
            id=row["id"],
            business_line_id=row["business_line_id"],
            scenario_id=row["scenario_id"],
            name=row["name"],
            base_version_id=row["base_version_id"],
            active=bool(row["active"]),
            created_at=datetime.fromisoformat(row["created_at"]).astimezone(UTC),
            metadata=json.loads(row["metadata"]),
        )
