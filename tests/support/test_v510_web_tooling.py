"""V5.10 console tooling tests."""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from checkpoint_ai import CheckpointAI
from checkpoint_ai.api import create_app
from checkpoint_ai.cli import main
from checkpoint_ai.console import ApprovalInbox, BackupManager, ConsoleReadModel
from checkpoint_ai.logs import SummaryLogStore
from checkpoint_ai.scenario import ScenarioStore


class V510WebToolingTest(unittest.TestCase):
    """Validate web console operator tooling."""

    def test_api_serve_command_invokes_uvicorn_with_requested_options(self) -> None:
        calls: list[dict[str, object]] = []

        def fake_run(app: str, **kwargs: object) -> None:
            calls.append({"app": app, **kwargs})

        with patch("checkpoint_ai.api._uvicorn_server.run", fake_run):
            status = main(["api", "serve", "--host", "127.0.0.1", "--port", "8123", "--reload"])

        self.assertEqual(status, 0)
        self.assertEqual(calls[0]["app"], "checkpoint_ai.api:create_app")
        self.assertEqual(calls[0]["host"], "127.0.0.1")
        self.assertEqual(calls[0]["port"], 8123)
        self.assertTrue(calls[0]["reload"])
        self.assertTrue(calls[0]["factory"])

    def test_seed_console_creates_human_actionable_demo_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "console.db"
            backup_dir = Path(tmp) / "backups"
            output = io.StringIO()

            with redirect_stdout(output):
                status = main(["--db", str(db_path), "demo", "seed-console", "--backup-dir", str(backup_dir)])

            snapshot = ConsoleReadModel(db_path).snapshot(
                scenario_id=None,
                allow_cross_scenario=True,
                reason="test",
            )
            scenarios = ScenarioStore(db_path).list()
            runs = SummaryLogStore(db_path).query_by_scenario("demo-quant")
            approvals = ApprovalInbox(db_path).list_items(scenario_id="demo-quant")
            backups = BackupManager(db_path, backup_dir).list_backups()

        self.assertEqual(status, 0)
        self.assertIn("Console demo seeded", output.getvalue())
        self.assertEqual(len(scenarios), 1)
        self.assertEqual(scenarios[0].id, "demo-quant")
        self.assertGreaterEqual(len(runs), 1)
        self.assertGreaterEqual(len(approvals), 1)
        self.assertGreaterEqual(len(backups), 1)
        self.assertEqual(snapshot.scenario_count, 1)
        self.assertGreaterEqual(snapshot.recent_run_count, 1)
        self.assertGreaterEqual(snapshot.pending_approval_count, 1)

    def test_api_app_accepts_initial_tokens_from_environment(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "console.db"
            with patch.dict("os.environ", {"CHECKPOINTAI_API_TOKENS": "dev-token, second-token"}):
                app = create_app(checkpoint_ai=CheckpointAI(sqlite_path=db_path), db_path=db_path)
            client = TestClient(app)

            response = client.get(
                "/api/health",
                headers={"Authorization": "Bearer dev-token"},
            )

        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
