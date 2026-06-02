"""Diagnostics tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from checkpoint_ai import CheckpointAI
from checkpoint_ai.diagnostics import HealthChecker
from checkpoint_ai.llm import LLMRequest, MiniMaxProvider
from checkpoint_ai.models import RunState


class FailingProvider(MiniMaxProvider):
    """Provider that fails health checks."""

    def generate(self, request: LLMRequest):  # type: ignore[no-untyped-def]
        """Raise a provider error."""

        raise RuntimeError("provider unavailable")


class DiagnosticsTest(unittest.TestCase):
    """Validate health checker reports actionable status."""

    def test_health_checker_reports_healthy_default_checkpoint_ai(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            checkpoint_ai = CheckpointAI(sqlite_path=Path(tmp) / "checkpoint_ai.db")
            checker = HealthChecker(checkpoint_ai=checkpoint_ai)

            report = checker.generate_diagnostic_report()

            self.assertEqual(report.overall_status, "healthy")
            self.assertGreaterEqual(len(report.checks), 6)
            self.assertTrue(any(check.component == "database" for check in report.checks))

    def test_health_checker_reports_provider_failure_with_recommendation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            checkpoint_ai = CheckpointAI(sqlite_path=Path(tmp) / "checkpoint_ai.db")
            checkpoint_ai.llm_provider = FailingProvider()
            checker = HealthChecker(checkpoint_ai=checkpoint_ai)

            report = checker.generate_diagnostic_report()

            self.assertEqual(report.overall_status, "unhealthy")
            provider_check = next(check for check in report.checks if check.component == "provider")
            self.assertEqual(provider_check.status, "error")
            self.assertIn("provider unavailable", provider_check.message)
            self.assertTrue(report.recommendations)

    def test_health_checker_detects_failed_recent_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            checkpoint_ai = CheckpointAI(sqlite_path=Path(tmp) / "checkpoint_ai.db")
            run = checkpoint_ai.create_run("failed run")
            run.state = RunState.FAILED
            checkpoint_ai.store.save_run(run)

            report = HealthChecker(checkpoint_ai=checkpoint_ai).generate_diagnostic_report()

            failed_check = next(check for check in report.checks if check.component == "recent_runs")
            self.assertEqual(failed_check.status, "warning")
            self.assertIn("failed", failed_check.message)


if __name__ == "__main__":
    unittest.main()
