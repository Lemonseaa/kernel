"""Workflow baseline persistence for evidence comparisons."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from pydantic import BaseModel


class EvidenceBaseline(BaseModel):
    """Current baseline for one external workflow."""

    workflow_id: str
    baseline_run_id: str
    reason: str
    created_at: str | None = None


class EvidenceBaselineStore:
    """SQLite store for workflow baselines."""

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
        with self._connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS evidence_baselines (
                    workflow_id TEXT PRIMARY KEY,
                    baseline_run_id TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )

    def set_baseline(self, workflow_id: str, baseline_run_id: str, reason: str) -> EvidenceBaseline:
        """Set or replace the baseline for one workflow."""

        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO evidence_baselines (workflow_id, baseline_run_id, reason)
                VALUES (?, ?, ?)
                ON CONFLICT(workflow_id) DO UPDATE SET
                    baseline_run_id=excluded.baseline_run_id,
                    reason=excluded.reason,
                    created_at=CURRENT_TIMESTAMP
                """,
                (workflow_id, baseline_run_id, reason),
            )
        loaded = self.get_baseline(workflow_id)
        if loaded is None:
            raise RuntimeError("Failed to persist evidence baseline")
        return loaded

    def get_baseline(self, workflow_id: str) -> EvidenceBaseline | None:
        """Return the current baseline for one workflow."""

        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT workflow_id, baseline_run_id, reason, created_at FROM evidence_baselines WHERE workflow_id = ?",
                (workflow_id,),
            ).fetchone()
        if row is None:
            return None
        return EvidenceBaseline(
            workflow_id=str(row["workflow_id"]),
            baseline_run_id=str(row["baseline_run_id"]),
            reason=str(row["reason"]),
            created_at=str(row["created_at"]) if row["created_at"] is not None else None,
        )
