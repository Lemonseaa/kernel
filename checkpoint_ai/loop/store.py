"""SQLite storage for Agent loop runs."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from checkpoint_ai.loop.models import LoopRun, LoopStatus


class AgentLoopStore:
    """Persist one-shot loop status and step logs."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def save(self, loop_run: LoopRun) -> str:
        """Create or update one loop run."""

        loop_run.updated_at = datetime.now(UTC)
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO agent_loops (
                    id, scenario_id, trigger_type, reason, trigger_payload, task,
                    status, steps, adapter_run_id, adapter_status,
                    adapter_value_summary, proposal_id, policy_level,
                    policy_action, shadow_result_id, baseline_comparison,
                    changed_summary, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    scenario_id=excluded.scenario_id,
                    trigger_type=excluded.trigger_type,
                    reason=excluded.reason,
                    trigger_payload=excluded.trigger_payload,
                    task=excluded.task,
                    status=excluded.status,
                    steps=excluded.steps,
                    adapter_run_id=excluded.adapter_run_id,
                    adapter_status=excluded.adapter_status,
                    adapter_value_summary=excluded.adapter_value_summary,
                    proposal_id=excluded.proposal_id,
                    policy_level=excluded.policy_level,
                    policy_action=excluded.policy_action,
                    shadow_result_id=excluded.shadow_result_id,
                    baseline_comparison=excluded.baseline_comparison,
                    changed_summary=excluded.changed_summary,
                    updated_at=excluded.updated_at
                """,
                self._to_row(loop_run),
            )
        return loop_run.id

    def get(self, loop_id: str) -> LoopRun | None:
        """Return one loop run by id."""

        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM agent_loops WHERE id = ?", (loop_id,)).fetchone()
        return None if row is None else self._from_row(row)

    def list(self, scenario_id: str | None = None) -> list[LoopRun]:
        """List loop runs, newest last."""

        where = "WHERE scenario_id = ?" if scenario_id is not None else ""
        params = (scenario_id,) if scenario_id is not None else ()
        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                f"SELECT * FROM agent_loops {where} ORDER BY created_at, rowid",
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
                CREATE TABLE IF NOT EXISTS agent_loops (
                    id TEXT PRIMARY KEY,
                    scenario_id TEXT NOT NULL,
                    trigger_type TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    trigger_payload TEXT NOT NULL,
                    task TEXT NOT NULL,
                    status TEXT NOT NULL,
                    steps TEXT NOT NULL,
                    adapter_run_id TEXT,
                    adapter_status TEXT,
                    adapter_value_summary TEXT,
                    proposal_id TEXT,
                    policy_level TEXT,
                    policy_action TEXT,
                    shadow_result_id TEXT,
                    baseline_comparison TEXT NOT NULL,
                    changed_summary TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_agent_loops_scenario ON agent_loops (scenario_id)"
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_agent_loops_status ON agent_loops (status)")

    @staticmethod
    def _to_row(loop_run: LoopRun) -> tuple[Any, ...]:
        return (
            loop_run.id,
            loop_run.scenario_id,
            loop_run.trigger_type,
            loop_run.reason,
            json.dumps(loop_run.trigger, ensure_ascii=False, default=str),
            loop_run.task,
            loop_run.status.value,
            json.dumps([step.model_dump(mode="json") for step in loop_run.steps], ensure_ascii=False),
            loop_run.adapter_run_id,
            loop_run.adapter_status,
            loop_run.adapter_value_summary,
            loop_run.proposal_id,
            loop_run.policy_level,
            loop_run.policy_action,
            loop_run.shadow_result_id,
            json.dumps(loop_run.baseline_comparison, ensure_ascii=False, default=str),
            loop_run.changed_summary,
            loop_run.created_at.isoformat(),
            loop_run.updated_at.isoformat(),
        )

    @staticmethod
    def _from_row(row: sqlite3.Row) -> LoopRun:
        return LoopRun(
            id=row["id"],
            scenario_id=row["scenario_id"],
            trigger_type=row["trigger_type"],
            reason=row["reason"],
            trigger=json.loads(row["trigger_payload"]),
            task=row["task"],
            status=LoopStatus(row["status"]),
            steps=json.loads(row["steps"]),
            adapter_run_id=row["adapter_run_id"],
            adapter_status=row["adapter_status"],
            adapter_value_summary=row["adapter_value_summary"],
            proposal_id=row["proposal_id"],
            policy_level=row["policy_level"],
            policy_action=row["policy_action"],
            shadow_result_id=row["shadow_result_id"],
            baseline_comparison=json.loads(row["baseline_comparison"]),
            changed_summary=row["changed_summary"],
            created_at=datetime.fromisoformat(row["created_at"]).astimezone(UTC),
            updated_at=datetime.fromisoformat(row["updated_at"]).astimezone(UTC),
        )
