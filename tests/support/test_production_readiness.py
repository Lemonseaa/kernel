"""Production readiness tests."""

from __future__ import annotations

import subprocess
import sys
import unittest

from tests.helpers import project_root


class ProductionReadinessTest(unittest.TestCase):
    """Validate production readiness scripts."""

    def test_benchmark_script_outputs_summary(self) -> None:
        root = project_root()
        result = subprocess.run(
            [sys.executable, "scripts/ops/benchmark.py", "--runs", "3"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("benchmark_summary", result.stdout)

    def test_security_audit_script_reports_no_critical_findings(self) -> None:
        root = project_root()
        result = subprocess.run(
            [sys.executable, "scripts/ops/security_audit.py"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("critical_findings=0", result.stdout)

    def test_stress_script_outputs_summary(self) -> None:
        root = project_root()
        result = subprocess.run(
            [sys.executable, "scripts/ops/stress_test.py", "--runs", "5", "--concurrency", "2"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("stress_summary", result.stdout)


if __name__ == "__main__":
    unittest.main()
