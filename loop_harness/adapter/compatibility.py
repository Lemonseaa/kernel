"""Adapter compatibility checklist and persistence."""

from __future__ import annotations

import json
import sqlite3
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class AdapterCompatibilityDecision(str, Enum):
    """Compatibility decision before writing adapter code."""

    GO = "go"
    NO_GO = "no_go"
    NEEDS_SPIKE = "needs_spike"


class AdapterCompatibilityInput(BaseModel):
    """Checklist input for an external Agent framework."""

    name: str
    structured_input: bool
    structured_output: bool
    prompt_slots: bool
    prompt_injection: bool
    shadow_run: bool
    run_trace: bool
    metrics_capture: bool
    metric_format_compatible: bool
    estimated_days: int
    dependencies: list[str] = Field(default_factory=list)


class AdapterCompatibilityReport(BaseModel):
    """Compatibility evaluation report."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    score: float
    decision: AdapterCompatibilityDecision
    blockers: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    markdown: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class AdapterCompatibilityEvaluator:
    """Evaluate whether an external framework is worth adapting."""

    def evaluate(self, candidate: AdapterCompatibilityInput) -> AdapterCompatibilityReport:
        """Return a compatibility report."""

        blockers: list[str] = []
        warnings: list[str] = []
        if not candidate.structured_input:
            blockers.append("structured_input")
        if not candidate.structured_output:
            blockers.append("structured_output")
        if not candidate.metrics_capture:
            blockers.append("metrics_capture")
        if not candidate.metric_format_compatible:
            warnings.append("metric_format_compatible")
        if not candidate.prompt_slots:
            warnings.append("prompt_slots")
        if not candidate.prompt_injection:
            warnings.append("prompt_injection")
        if not candidate.shadow_run:
            warnings.append("shadow_run")
        if not candidate.run_trace:
            warnings.append("run_trace")
        if candidate.estimated_days > 5:
            warnings.append("estimated_days")
        score = self._score(candidate)
        if blockers:
            decision = AdapterCompatibilityDecision.NO_GO
        elif candidate.estimated_days > 5 or warnings:
            decision = AdapterCompatibilityDecision.NEEDS_SPIKE
        elif score >= 0.75:
            decision = AdapterCompatibilityDecision.GO
        else:
            decision = AdapterCompatibilityDecision.NEEDS_SPIKE
        return AdapterCompatibilityReport(
            name=candidate.name,
            score=score,
            decision=decision,
            blockers=blockers,
            warnings=warnings,
            markdown=self._markdown(candidate.name, score, decision, blockers, warnings),
        )

    @staticmethod
    def _score(candidate: AdapterCompatibilityInput) -> float:
        checks = [
            candidate.structured_input,
            candidate.structured_output,
            candidate.prompt_slots,
            candidate.prompt_injection,
            candidate.shadow_run,
            candidate.run_trace,
            candidate.metrics_capture,
            candidate.metric_format_compatible,
        ]
        effort_penalty = 0.0 if candidate.estimated_days <= 5 else 0.15
        return round(max(0.0, (sum(1 for check in checks if check) / len(checks)) - effort_penalty), 4)

    @staticmethod
    def _markdown(
        name: str,
        score: float,
        decision: AdapterCompatibilityDecision,
        blockers: list[str],
        warnings: list[str],
    ) -> str:
        return "\n".join(
            [
                f"# Adapter Compatibility Report: {name}",
                "",
                f"score: {score}",
                f"decision: {decision.value}",
                f"blockers: {blockers}",
                f"warnings: {warnings}",
            ]
        )


class AdapterCompatibilityReportStore:
    """Persist adapter compatibility reports."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def save(self, report: AdapterCompatibilityReport) -> str:
        """Save one report."""

        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO adapter_compatibility_reports (
                    id, name, score, decision, blockers, warnings, markdown, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name=excluded.name,
                    score=excluded.score,
                    decision=excluded.decision,
                    blockers=excluded.blockers,
                    warnings=excluded.warnings,
                    markdown=excluded.markdown
                """,
                self._to_row(report),
            )
        return report.id

    def get(self, report_id: str) -> AdapterCompatibilityReport | None:
        """Return one report by id."""

        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM adapter_compatibility_reports WHERE id = ?",
                (report_id,),
            ).fetchone()
        return None if row is None else self._from_row(row)

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
                CREATE TABLE IF NOT EXISTS adapter_compatibility_reports (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    score REAL NOT NULL,
                    decision TEXT NOT NULL,
                    blockers TEXT NOT NULL,
                    warnings TEXT NOT NULL,
                    markdown TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )

    @staticmethod
    def _to_row(report: AdapterCompatibilityReport) -> tuple[Any, ...]:
        return (
            report.id,
            report.name,
            report.score,
            report.decision.value,
            json.dumps(report.blockers, ensure_ascii=False),
            json.dumps(report.warnings, ensure_ascii=False),
            report.markdown,
            report.created_at.isoformat(),
        )

    @staticmethod
    def _from_row(row: sqlite3.Row) -> AdapterCompatibilityReport:
        return AdapterCompatibilityReport(
            id=row["id"],
            name=row["name"],
            score=row["score"],
            decision=AdapterCompatibilityDecision(row["decision"]),
            blockers=json.loads(row["blockers"]),
            warnings=json.loads(row["warnings"]),
            markdown=row["markdown"],
            created_at=datetime.fromisoformat(row["created_at"]).astimezone(UTC),
        )
