"""API and health check tests."""

from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

from kernel.api import create_app


class ApiHealthTest(unittest.TestCase):
    """Validate optional API surface and health script."""

    def test_create_app_returns_fastapi_or_fallback_app(self) -> None:
        app = create_app()

        self.assertTrue(hasattr(app, "routes") or hasattr(app, "kernel"))

    def test_health_check_script_exits_successfully(self) -> None:
        root = Path(__file__).resolve().parents[1]

        result = subprocess.run(
            [sys.executable, "scripts/health_check.py"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("healthy", result.stdout.lower())
