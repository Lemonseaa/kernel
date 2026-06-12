"""Baseline management for experiment comparisons."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class Baseline(BaseModel):
    """Baseline metric snapshot."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    business_line_id: str | None = None
    name: str
    metrics: dict[str, Any] = Field(default_factory=dict)
    experiment_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    is_active: bool = True


class BaselineManager:
    """基线管理器。"""

    def __init__(self, storage: str | Path) -> None:
        """Create a SQLite-backed baseline manager."""

        self.path = Path(storage)
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
        with self._connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS baselines (
                    id TEXT PRIMARY KEY,
                    business_line_id TEXT,
                    name TEXT NOT NULL,
                    metrics TEXT NOT NULL,
                    experiment_id TEXT,
                    created_at TEXT NOT NULL,
                    is_active INTEGER NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_baselines_bl ON baselines (business_line_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_baselines_active ON baselines (is_active)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_baselines_created ON baselines (created_at)")

    def create(
        self,
        metrics: dict[str, Any],
        name: str | None = None,
        business_line_id: str | None = None,
        experiment_id: str | None = None,
    ) -> str:
        """创建新基线。"""

        baseline = Baseline(
            business_line_id=business_line_id,
            name=name or f"baseline-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}",
            metrics=metrics,
            experiment_id=experiment_id,
            is_active=True,
        )
        with self._connection() as conn:
            self._deactivate_for_business_line(conn, business_line_id)
            conn.execute(
                """
                INSERT INTO baselines (
                    id, business_line_id, name, metrics, experiment_id, created_at, is_active
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                self._to_row(baseline),
            )
        return baseline.id

    def get(self, baseline_id: str) -> Baseline | None:
        """Return one baseline by id."""

        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM baselines WHERE id = ?", (baseline_id,)).fetchone()
        return None if row is None else self._from_row(row)

    def get_active(self, business_line_id: str | None = None) -> Baseline | None:
        """获取当前活跃基线。"""

        if business_line_id is None:
            sql = """
                SELECT * FROM baselines
                WHERE is_active = 1 AND business_line_id IS NULL
                ORDER BY created_at DESC, rowid DESC
                LIMIT 1
            """
            params: tuple[Any, ...] = ()
        else:
            sql = """
                SELECT * FROM baselines
                WHERE is_active = 1 AND business_line_id = ?
                ORDER BY created_at DESC, rowid DESC
                LIMIT 1
            """
            params = (business_line_id,)
        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(sql, params).fetchone()
        return None if row is None else self._from_row(row)

    def set_active(self, baseline_id: str) -> bool:
        """设置为活跃基线。"""

        baseline = self.get(baseline_id)
        if baseline is None:
            return False
        with self._connection() as conn:
            self._deactivate_for_business_line(conn, baseline.business_line_id)
            conn.execute("UPDATE baselines SET is_active = 1 WHERE id = ?", (baseline_id,))
        return True

    def list(self, business_line_id: str | None = None) -> list[Baseline]:
        """列出所有基线。"""

        if business_line_id is None:
            sql = "SELECT * FROM baselines ORDER BY created_at, rowid"
            params: tuple[Any, ...] = ()
        else:
            sql = "SELECT * FROM baselines WHERE business_line_id = ? ORDER BY created_at, rowid"
            params = (business_line_id,)
        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(sql, params).fetchall()
        return [self._from_row(row) for row in rows]

    @staticmethod
    def _deactivate_for_business_line(conn: sqlite3.Connection, business_line_id: str | None) -> None:
        if business_line_id is None:
            conn.execute("UPDATE baselines SET is_active = 0 WHERE business_line_id IS NULL")
            return
        conn.execute("UPDATE baselines SET is_active = 0 WHERE business_line_id = ?", (business_line_id,))

    @staticmethod
    def _to_row(baseline: Baseline) -> tuple[Any, ...]:
        return (
            baseline.id,
            baseline.business_line_id,
            baseline.name,
            json.dumps(baseline.metrics, ensure_ascii=False, default=str),
            baseline.experiment_id,
            baseline.created_at.isoformat(),
            1 if baseline.is_active else 0,
        )

    @staticmethod
    def _from_row(row: sqlite3.Row) -> Baseline:
        return Baseline(
            id=row["id"],
            business_line_id=row["business_line_id"],
            name=row["name"],
            metrics=json.loads(row["metrics"]),
            experiment_id=row["experiment_id"],
            created_at=datetime.fromisoformat(row["created_at"]).astimezone(UTC),
            is_active=bool(row["is_active"]),
        )
