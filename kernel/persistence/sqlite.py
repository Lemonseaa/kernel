"""SQLite storage implementation."""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from kernel.models import Run, Task
from kernel.persistence.store import Storage


class SQLiteStore(Storage):
    """Persist run and task state in SQLite."""

    def __init__(self, path: str | Path) -> None:
        """Create or open a SQLite store."""

        self.path = Path(path)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        """Open a SQLite connection."""

        return sqlite3.connect(self.path)

    def _init_schema(self) -> None:
        """Create tables if they do not exist."""

        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY,
                    user_request TEXT NOT NULL,
                    state TEXT NOT NULL,
                    metadata TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    run_id TEXT,
                    name TEXT NOT NULL,
                    agent_capability TEXT NOT NULL,
                    state TEXT NOT NULL,
                    input TEXT,
                    output_artifact_id TEXT,
                    error TEXT,
                    metadata TEXT NOT NULL
                )
                """
            )

    def save_run(self, run: Run) -> None:
        """Persist a run and all attached tasks."""

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO runs (id, user_request, state, metadata)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    user_request=excluded.user_request,
                    state=excluded.state,
                    metadata=excluded.metadata
                """,
                (run.id, run.user_request, run.state.value, json.dumps(run.metadata)),
            )
        for task in run.tasks:
            self.save_task(task)

    def save_task(self, task: Task) -> None:
        """Persist a task."""

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO tasks (
                    id, run_id, name, agent_capability, state, input,
                    output_artifact_id, error, metadata
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    run_id=excluded.run_id,
                    name=excluded.name,
                    agent_capability=excluded.agent_capability,
                    state=excluded.state,
                    input=excluded.input,
                    output_artifact_id=excluded.output_artifact_id,
                    error=excluded.error,
                    metadata=excluded.metadata
                """,
                (
                    task.id,
                    task.run_id,
                    task.name,
                    task.agent_capability,
                    task.state.value,
                    json.dumps(task.input),
                    task.output_artifact_id,
                    task.error,
                    json.dumps(task.metadata),
                ),
            )

    def load_run(self, run_id: str) -> dict[str, Any]:
        """Load a run row as a dict."""

        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        if row is None:
            raise KeyError(f"Run not found: {run_id}")
        result = dict(row)
        result["metadata"] = json.loads(result["metadata"])
        return result

    def load_task(self, task_id: str) -> dict[str, Any]:
        """Load a task row as a dict."""

        with self._connect() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if row is None:
            raise KeyError(f"Task not found: {task_id}")
        result = dict(row)
        result["metadata"] = json.loads(result["metadata"])
        result["input"] = json.loads(result["input"]) if result["input"] is not None else None
        return result
