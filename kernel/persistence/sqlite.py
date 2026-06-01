"""SQLite storage implementation."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from kernel.models import Run, Task
from kernel.persistence.store import Storage


class SQLiteStore(Storage):
    """Persist run and task state in SQLite."""

    def __init__(self, path: str | Path) -> None:
        """Create or open a SQLite store."""

        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        """Open a SQLite connection."""

        return sqlite3.connect(self.path)

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        """Open a SQLite connection and close it after use."""

        conn = self._connect()
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_schema(self) -> None:
        """Create tables if they do not exist."""

        with self._connection() as conn:
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
                    result TEXT,
                    metadata TEXT NOT NULL
                )
                """
            )
            columns = {
                row[1]
                for row in conn.execute("PRAGMA table_info(tasks)").fetchall()
            }
            if "result" not in columns:
                conn.execute("ALTER TABLE tasks ADD COLUMN result TEXT")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    content TEXT NOT NULL
                )
                """
            )

    def save_run(self, run: Run) -> None:
        """Persist a run and all attached tasks."""

        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO runs (id, user_request, state, metadata)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    user_request=excluded.user_request,
                    state=excluded.state,
                    metadata=excluded.metadata
                """,
                (run.id, run.user_request, run.state.value, self._to_json(run.metadata)),
            )
        for task in run.tasks:
            self.save_task(task)

    def save_task(self, task: Task) -> None:
        """Persist a task."""

        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO tasks (
                    id, run_id, name, agent_capability, state, input,
                    output_artifact_id, error, result, metadata
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    run_id=excluded.run_id,
                    name=excluded.name,
                    agent_capability=excluded.agent_capability,
                    state=excluded.state,
                    input=excluded.input,
                    output_artifact_id=excluded.output_artifact_id,
                    error=excluded.error,
                    result=excluded.result,
                    metadata=excluded.metadata
                """,
                (
                    task.id,
                    task.run_id,
                    task.name,
                    task.agent_capability,
                    task.state.value,
                    self._to_json(task.input),
                    task.output_artifact_id,
                    task.error,
                    self._to_json(task.result),
                    self._to_json(task.metadata),
                ),
            )

    def load_run(self, run_id: str) -> dict[str, Any]:
        """Load a run row as a dict."""

        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM runs WHERE id = ?", (run_id,)).fetchone()
        if row is None:
            raise KeyError(f"Run not found: {run_id}")
        result = dict(row)
        result["metadata"] = json.loads(result["metadata"])
        return result

    def load_task(self, task_id: str) -> dict[str, Any]:
        """Load a task row as a dict."""

        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if row is None:
            raise KeyError(f"Task not found: {task_id}")
        result = dict(row)
        result["metadata"] = json.loads(result["metadata"])
        result["input"] = json.loads(result["input"]) if result["input"] is not None else None
        result["result"] = json.loads(result["result"]) if result.get("result") is not None else None
        return result

    def list_runs(self) -> list[dict[str, Any]]:
        """List persisted runs ordered by insertion row id."""

        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM runs ORDER BY rowid").fetchall()
        results = []
        for row in rows:
            item = dict(row)
            item["metadata"] = json.loads(item["metadata"])
            results.append(item)
        return results

    def list_tasks(self, run_id: str | None = None) -> list[dict[str, Any]]:
        """List persisted tasks ordered by insertion row id."""

        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            if run_id is None:
                rows = conn.execute("SELECT * FROM tasks ORDER BY rowid").fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM tasks WHERE run_id = ? ORDER BY rowid",
                    (run_id,),
                ).fetchall()
        return [self._task_row_to_dict(row) for row in rows]

    def save_memory(self, run_id: str, task_id: str, content: Any) -> None:
        """Persist one memory item."""

        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO memory (run_id, task_id, content)
                VALUES (?, ?, ?)
                """,
                (run_id, task_id, self._to_json(content)),
            )

    def list_memory(self, run_id: str) -> list[dict[str, Any]]:
        """List memory items for one run."""

        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT run_id, task_id, content FROM memory WHERE run_id = ? ORDER BY id",
                (run_id,),
            ).fetchall()
        return [
            {
                "run_id": row["run_id"],
                "task_id": row["task_id"],
                "content": json.loads(row["content"]),
            }
            for row in rows
        ]

    @staticmethod
    def _task_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        """Convert a SQLite task row into a typed dict."""

        result = dict(row)
        result["metadata"] = json.loads(result["metadata"])
        result["input"] = json.loads(result["input"]) if result["input"] is not None else None
        result["result"] = json.loads(result["result"]) if result.get("result") is not None else None
        return result

    @staticmethod
    def _to_json(value: Any) -> str:
        """Serialize values safely for SQLite JSON text fields."""

        return json.dumps(value, default=str, ensure_ascii=False)
