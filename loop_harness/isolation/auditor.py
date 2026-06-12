"""Scenario isolation audit helpers."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Literal

from pydantic import BaseModel


class IsolationCheckResult(BaseModel):
    """One store isolation check result."""

    store_name: str
    scenario_ids: list[str]
    missing_scenario_id_count: int
    status: Literal["ok", "warning"]


class ScenarioIsolationAuditor:
    """Audit scenario ids in SQLite-backed stores."""

    TABLES = [
        "raw_logs",
        "summary_logs",
        "shadow_results",
        "prompt_proposals",
        "proposals",
        "prompt_versions",
        "scenario_metric_schemas",
        "version_recommendations",
        "parameter_suggestions",
        "agent_loops",
    ]

    def audit_sqlite(self, db_path: str | Path) -> list[IsolationCheckResult]:
        """Return scenario-id coverage for known tables."""

        path = Path(db_path)
        if not path.exists():
            return []
        results: list[IsolationCheckResult] = []
        with closing(sqlite3.connect(path)) as conn:
            conn.row_factory = sqlite3.Row
            existing_tables = {
                row["name"]
                for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            }
            for table in self.TABLES:
                if table not in existing_tables:
                    continue
                columns = {row["name"] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
                if "scenario_id" not in columns:
                    results.append(
                        IsolationCheckResult(
                            store_name=table,
                            scenario_ids=[],
                            missing_scenario_id_count=0,
                            status="warning",
                        )
                    )
                    continue
                scenario_rows = conn.execute(
                    f"SELECT DISTINCT scenario_id FROM {table} WHERE scenario_id IS NOT NULL AND scenario_id != ''"
                ).fetchall()
                missing = conn.execute(
                    f"SELECT COUNT(*) AS count FROM {table} WHERE scenario_id IS NULL OR scenario_id = ''"
                ).fetchone()["count"]
                results.append(
                    IsolationCheckResult(
                        store_name=table,
                        scenario_ids=sorted(str(row["scenario_id"]) for row in scenario_rows),
                        missing_scenario_id_count=int(missing),
                        status="ok" if int(missing) == 0 else "warning",
                    )
                )
        return results
