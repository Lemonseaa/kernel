"""SQLite storage for external workflow evidence."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from checkpoint_ai.evidence.models import (
    EvidenceReport,
    ExternalWorkflowRun,
    StoredEvidenceRun,
    WorkflowVisualization,
)


class EvidenceStore:
    """Persist imported workflow runs and derived evidence objects."""

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
                CREATE TABLE IF NOT EXISTS evidence_runs (
                    run_id TEXT PRIMARY KEY,
                    workflow_id TEXT NOT NULL,
                    run_kind TEXT NOT NULL,
                    run_json TEXT NOT NULL,
                    visualization_json TEXT NOT NULL,
                    report_json TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_evidence_workflow ON evidence_runs (workflow_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_evidence_kind ON evidence_runs (run_kind)")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS evidence_comparison_reports (
                    report_id TEXT PRIMARY KEY,
                    workflow_id TEXT NOT NULL,
                    baseline_run_id TEXT NOT NULL,
                    candidate_run_id TEXT NOT NULL,
                    report_json TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_evidence_comparison_workflow
                ON evidence_comparison_reports (workflow_id)
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_evidence_comparison_runs
                ON evidence_comparison_reports (baseline_run_id, candidate_run_id)
                """
            )

    def save(self, run: ExternalWorkflowRun, visualization: WorkflowVisualization, report: EvidenceReport) -> str:
        """Insert or update one external workflow run."""

        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO evidence_runs (
                    run_id, workflow_id, run_kind, run_json, visualization_json, report_json
                )
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(run_id) DO UPDATE SET
                    workflow_id=excluded.workflow_id,
                    run_kind=excluded.run_kind,
                    run_json=excluded.run_json,
                    visualization_json=excluded.visualization_json,
                    report_json=excluded.report_json
                """,
                (
                    run.run_id,
                    run.workflow_id,
                    run.run_kind.value,
                    run.model_dump_json(),
                    visualization.model_dump_json(),
                    report.model_dump_json(),
                ),
            )
        return run.run_id

    def get_run(self, run_id: str) -> StoredEvidenceRun | None:
        """Return one stored evidence run."""

        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM evidence_runs WHERE run_id = ?", (run_id,)).fetchone()
        if row is None:
            return None
        return self._from_row(row)

    def list_runs(self, workflow_id: str | None = None) -> list[StoredEvidenceRun]:
        """List stored evidence runs."""

        params: list[Any] = []
        where = ""
        if workflow_id is not None:
            where = "WHERE workflow_id = ?"
            params.append(workflow_id)
        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                f"SELECT * FROM evidence_runs {where} ORDER BY created_at, rowid",
                tuple(params),
            ).fetchall()
        return [self._from_row(row) for row in rows]

    def save_comparison_report(self, report: EvidenceReport) -> str:
        """Insert or update one baseline/candidate comparison report."""

        if report.baseline_run_id is None or report.candidate_run_id is None:
            raise ValueError("Comparison report requires baseline_run_id and candidate_run_id")
        report_id = self._comparison_report_id(report.baseline_run_id, report.candidate_run_id)
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO evidence_comparison_reports (
                    report_id, workflow_id, baseline_run_id, candidate_run_id, report_json
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(report_id) DO UPDATE SET
                    workflow_id=excluded.workflow_id,
                    baseline_run_id=excluded.baseline_run_id,
                    candidate_run_id=excluded.candidate_run_id,
                    report_json=excluded.report_json
                """,
                (
                    report_id,
                    report.workflow_id,
                    report.baseline_run_id,
                    report.candidate_run_id,
                    report.model_dump_json(),
                ),
            )
        return report_id

    def get_comparison_report(self, baseline_run_id: str, candidate_run_id: str) -> EvidenceReport | None:
        """Return one stored comparison report."""

        report_id = self._comparison_report_id(baseline_run_id, candidate_run_id)
        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT report_json FROM evidence_comparison_reports WHERE report_id = ?",
                (report_id,),
            ).fetchone()
        if row is None:
            return None
        return EvidenceReport.model_validate(json.loads(row["report_json"]))

    def list_comparison_reports(self, workflow_id: str | None = None) -> list[EvidenceReport]:
        """List stored comparison reports."""

        params: list[Any] = []
        where = ""
        if workflow_id is not None:
            where = "WHERE workflow_id = ?"
            params.append(workflow_id)
        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                f"SELECT report_json FROM evidence_comparison_reports {where} ORDER BY created_at, rowid",
                tuple(params),
            ).fetchall()
        return [EvidenceReport.model_validate(json.loads(row["report_json"])) for row in rows]

    @staticmethod
    def _from_row(row: sqlite3.Row) -> StoredEvidenceRun:
        return StoredEvidenceRun(
            run=ExternalWorkflowRun.model_validate(json.loads(row["run_json"])),
            visualization=WorkflowVisualization.model_validate(json.loads(row["visualization_json"])),
            report=EvidenceReport.model_validate(json.loads(row["report_json"])),
        )

    @staticmethod
    def _comparison_report_id(baseline_run_id: str, candidate_run_id: str) -> str:
        return f"{baseline_run_id}::{candidate_run_id}"
