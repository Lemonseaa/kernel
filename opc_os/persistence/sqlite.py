"""SQLite storage implementation."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path
from typing import Any

from opc_os.businessline.models import (
    BusinessLine,
    BusinessLineConfig,
    BusinessLineStatus,
    ResourceLimits,
)
from opc_os.models import Run, Task
from opc_os.persistence.store import Storage


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
                    business_line_id TEXT NOT NULL DEFAULT 'default',
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
                    business_line_id TEXT NOT NULL DEFAULT 'default',
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
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS business_lines (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    config TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    last_active_at REAL NOT NULL
                )
                """
            )
            run_columns = {
                row[1]
                for row in conn.execute("PRAGMA table_info(runs)").fetchall()
            }
            if "business_line_id" not in run_columns:
                conn.execute("ALTER TABLE runs ADD COLUMN business_line_id TEXT NOT NULL DEFAULT 'default'")
            columns = {
                row[1]
                for row in conn.execute("PRAGMA table_info(tasks)").fetchall()
            }
            if "business_line_id" not in columns:
                conn.execute("ALTER TABLE tasks ADD COLUMN business_line_id TEXT NOT NULL DEFAULT 'default'")
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
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS context_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    business_line_id TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    content TEXT NOT NULL
                )
                """
            )

    def save_run(self, run: Run) -> None:
        """Persist a run and all attached tasks."""

        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO runs (id, business_line_id, user_request, state, metadata)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    business_line_id=excluded.business_line_id,
                    user_request=excluded.user_request,
                    state=excluded.state,
                    metadata=excluded.metadata
                """,
                (
                    run.id,
                    run.business_line_id,
                    run.user_request,
                    run.state.value,
                    self._to_json(run.metadata),
                ),
            )
        for task in run.tasks:
            self.save_task(task)

    def save_task(self, task: Task) -> None:
        """Persist a task."""

        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO tasks (
                    id, business_line_id, run_id, name, agent_capability, state, input,
                    output_artifact_id, error, result, metadata
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    business_line_id=excluded.business_line_id,
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
                    task.business_line_id,
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

    def save_business_line(self, business_line: BusinessLine) -> None:
        """Persist a BusinessLine."""

        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO business_lines (id, name, status, config, created_at, last_active_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,
                    status=excluded.status,
                    config=excluded.config,
                    created_at=excluded.created_at,
                    last_active_at=excluded.last_active_at
                """,
                (
                    business_line.id,
                    business_line.name,
                    business_line.status.value,
                    self._to_json(asdict(business_line.config)),
                    business_line.created_at,
                    business_line.last_active_at,
                ),
            )

    def load_business_line(self, business_line_id: str) -> BusinessLine:
        """Load a BusinessLine by id."""

        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM business_lines WHERE id = ?",
                (business_line_id,),
            ).fetchone()
        if row is None:
            raise KeyError(f"BusinessLine not found: {business_line_id}")
        return self._business_line_row_to_model(row)

    def list_business_lines(self, status: BusinessLineStatus | None = None) -> list[BusinessLine]:
        """List BusinessLines ordered by insertion row id."""

        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            if status is None:
                rows = conn.execute("SELECT * FROM business_lines ORDER BY rowid").fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM business_lines WHERE status = ? ORDER BY rowid",
                    (status.value,),
                ).fetchall()
        return [self._business_line_row_to_model(row) for row in rows]

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

    def list_runs(self, business_line_id: str | None = None) -> list[dict[str, Any]]:
        """List persisted runs ordered by insertion row id."""

        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            if business_line_id is None:
                rows = conn.execute("SELECT * FROM runs ORDER BY rowid").fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM runs WHERE business_line_id = ? ORDER BY rowid",
                    (business_line_id,),
                ).fetchall()
        results = []
        for row in rows:
            item = dict(row)
            item["metadata"] = json.loads(item["metadata"])
            results.append(item)
        return results

    def list_tasks(
        self,
        run_id: str | None = None,
        business_line_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """List persisted tasks ordered by insertion row id."""

        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            if run_id is not None and business_line_id is not None:
                rows = conn.execute(
                    """
                    SELECT * FROM tasks
                    WHERE run_id = ? AND business_line_id = ?
                    ORDER BY rowid
                    """,
                    (run_id, business_line_id),
                ).fetchall()
            elif run_id is not None:
                rows = conn.execute(
                    "SELECT * FROM tasks WHERE run_id = ? ORDER BY rowid",
                    (run_id,),
                ).fetchall()
            elif business_line_id is not None:
                rows = conn.execute(
                    "SELECT * FROM tasks WHERE business_line_id = ? ORDER BY rowid",
                    (business_line_id,),
                ).fetchall()
            else:
                rows = conn.execute("SELECT * FROM tasks ORDER BY rowid").fetchall()
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

    def save_context_item(
        self,
        business_line_id: str,
        run_id: str,
        task_id: str,
        kind: str,
        content: Any,
    ) -> None:
        """Persist one BusinessLine-scoped context item."""

        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO context_items (business_line_id, run_id, task_id, kind, content)
                VALUES (?, ?, ?, ?, ?)
                """,
                (business_line_id, run_id, task_id, kind, self._to_json(content)),
            )

    def list_context_items(
        self,
        business_line_id: str,
        kind: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """List BusinessLine-scoped context items ordered from oldest to newest."""

        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            if kind is None:
                sql = """
                    SELECT id, business_line_id, run_id, task_id, kind, content
                    FROM context_items
                    WHERE business_line_id = ?
                    ORDER BY id
                """
                params: tuple[object, ...] = (business_line_id,)
            else:
                sql = """
                    SELECT id, business_line_id, run_id, task_id, kind, content
                    FROM context_items
                    WHERE business_line_id = ? AND kind = ?
                    ORDER BY id
                """
                params = (business_line_id, kind)
            if limit is not None:
                sql = f"SELECT * FROM ({sql}) ORDER BY id DESC LIMIT ?"
                params = (*params, limit)
            rows = conn.execute(sql, params).fetchall()
        items = [
            {
                "business_line_id": row["business_line_id"],
                "run_id": row["run_id"],
                "task_id": row["task_id"],
                "kind": row["kind"],
                "content": json.loads(row["content"]),
            }
            for row in rows
        ]
        if limit is not None:
            items.reverse()
        return items

    @staticmethod
    def _task_row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        """Convert a SQLite task row into a typed dict."""

        result = dict(row)
        result["metadata"] = json.loads(result["metadata"])
        result["input"] = json.loads(result["input"]) if result["input"] is not None else None
        result["result"] = json.loads(result["result"]) if result.get("result") is not None else None
        return result

    @staticmethod
    def _business_line_row_to_model(row: sqlite3.Row) -> BusinessLine:
        """Convert a SQLite BusinessLine row into a model."""

        config = json.loads(row["config"])
        resource_limits = config.get("resource_limits", {})
        return BusinessLine(
            id=row["id"],
            name=row["name"],
            status=BusinessLineStatus(row["status"]),
            config=BusinessLineConfig(
                evaluation_rules=list(config.get("evaluation_rules", [])),
                agent_templates=list(config.get("agent_templates", [])),
                workflow_templates=list(config.get("workflow_templates", [])),
                policy_ids=list(config.get("policy_ids", [])),
                resource_limits=ResourceLimits(
                    max_concurrent_runs=resource_limits.get("max_concurrent_runs", 10),
                    max_agents=resource_limits.get("max_agents", 50),
                ),
            ),
            created_at=row["created_at"],
            last_active_at=row["last_active_at"],
        )

    @staticmethod
    def _to_json(value: Any) -> str:
        """Serialize values safely for SQLite JSON text fields."""

        return json.dumps(value, default=str, ensure_ascii=False)
