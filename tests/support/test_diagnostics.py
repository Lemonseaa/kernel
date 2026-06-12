"""Diagnostics tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from loop_harness import LoopHarness
from loop_harness.diagnostics import HealthChecker
from loop_harness.llm import LLMRequest, MiniMaxProvider
from loop_harness.models import RunState


class FailingProvider(MiniMaxProvider):
    """Provider that fails health checks."""

    def generate(self, request: LLMRequest):  # type: ignore[no-untyped-def]
        """Raise a provider error."""

        raise RuntimeError("provider unavailable")


class DiagnosticsTest(unittest.TestCase):
    """Validate health checker reports actionable status."""

    def test_health_checker_reports_healthy_default_loop_harness(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            loop_harness = LoopHarness(sqlite_path=Path(tmp) / "loop_harness.db")
            checker = HealthChecker(loop_harness=loop_harness)

            report = checker.generate_diagnostic_report()

            self.assertEqual(report.overall_status, "healthy")
            self.assertGreaterEqual(len(report.checks), 6)
            self.assertTrue(any(check.component == "database" for check in report.checks))

    def test_health_checker_reports_provider_failure_with_recommendation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            loop_harness = LoopHarness(sqlite_path=Path(tmp) / "loop_harness.db")
            loop_harness.llm_provider = FailingProvider()
            checker = HealthChecker(loop_harness=loop_harness)

            report = checker.generate_diagnostic_report()

            self.assertEqual(report.overall_status, "unhealthy")
            provider_check = next(check for check in report.checks if check.component == "provider")
            self.assertEqual(provider_check.status, "error")
            self.assertIn("provider unavailable", provider_check.message)
            self.assertTrue(report.recommendations)

    def test_health_checker_detects_failed_recent_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            loop_harness = LoopHarness(sqlite_path=Path(tmp) / "loop_harness.db")
            run = loop_harness.create_run("failed run")
            run.state = RunState.FAILED
            loop_harness.store.save_run(run)

            report = HealthChecker(loop_harness=loop_harness).generate_diagnostic_report()

            failed_check = next(check for check in report.checks if check.component == "recent_runs")
            self.assertEqual(failed_check.status, "warning")
            self.assertIn("failed", failed_check.message)


if __name__ == "__main__":
    unittest.main()
