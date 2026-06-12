"""Clean Evidence Harness facade.

This is the mainline product entrypoint. It intentionally wraps only evidence
storage and service operations, without constructing the legacy agent runtime,
workflow engine, tool registry, or runtime policy stack.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from checkpoint_ai.evidence import (
    EvidenceReport,
    EvidenceService,
    EvidenceStore,
    IngestResult,
    StoredEvidenceRun,
    WorkflowVisualization,
)


class EvidenceHarness:
    """Small facade for external workflow evidence ingestion and review."""

    def __init__(self, sqlite_path: str | Path) -> None:
        self.store = EvidenceStore(sqlite_path)
        self.service = EvidenceService(self.store)

    def ingest_file(self, path: str | Path) -> IngestResult:
        """Ingest one external workflow run JSON file."""

        return self.service.ingest_file(path)

    def ingest_payload(self, payload: dict[str, Any]) -> IngestResult:
        """Ingest one external workflow run payload."""

        return self.service.ingest_payload(payload)

    def visualize(self, run_id: str) -> WorkflowVisualization:
        """Return stored visualization data for one run."""

        stored = self.store.get_run(run_id)
        if stored is None:
            raise ValueError(f"Unknown evidence run: {run_id}")
        return stored.visualization

    def report(self, run_id: str) -> EvidenceReport:
        """Return stored evidence report for one run."""

        stored = self.store.get_run(run_id)
        if stored is None:
            raise ValueError(f"Unknown evidence run: {run_id}")
        return stored.report

    def compare(self, baseline_run_id: str, candidate_run_id: str) -> EvidenceReport:
        """Compare a candidate run against a baseline run."""

        return self.service.compare(baseline_run_id, candidate_run_id)

    def list_runs(self, workflow_id: str | None = None) -> list[StoredEvidenceRun]:
        """List stored evidence runs, optionally scoped by workflow."""

        return self.store.list_runs(workflow_id=workflow_id)
