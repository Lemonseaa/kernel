"""V6.6 autonomy console API tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from loop_harness.api import create_app
from loop_harness.auth import APIKeyManager
from loop_harness.autonomy import AutonomyActionStatus, AutonomyActionStore
from loop_harness.decision import DecisionKind, DecisionLogStore


class V66AutonomyConsoleApiTest(unittest.TestCase):
    """Validate operator-visible autonomy queue controls."""

    def test_autonomy_api_lists_actions_and_processes_one_with_audit_result(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "console.db"
            store = AutonomyActionStore(db_path)
            action = store.create(
                scenario_id="demo-quant",
                proposal_id="proposal-1",
                action_type="prompt_patch",
                checkpoint_id="checkpoint-1",
                reason="Historical shadow passed and patch is low-risk.",
            )
            client, token = self._client(db_path)
            headers = self._auth(token)

            listed = client.get("/api/autonomy/actions", headers=headers)
            detail = client.get(f"/api/autonomy/actions/{action.id}", headers=headers)
            processed = client.post(f"/api/autonomy/actions/{action.id}/process", headers=headers)
            loaded = store.get(action.id)
            decisions = DecisionLogStore(db_path).list(source_id=action.id)

        self.assertEqual(listed.status_code, 200)
        self.assertEqual([row["id"] for row in listed.json()], [action.id])
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["checkpoint_id"], "checkpoint-1")
        self.assertEqual(processed.status_code, 200)
        self.assertEqual(processed.json()["action"]["id"], action.id)
        self.assertEqual(processed.json()["action"]["status"], AutonomyActionStatus.SUCCEEDED.value)
        self.assertEqual(processed.json()["action"]["result"]["mode"], "audit_only")
        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertEqual(loaded.status, AutonomyActionStatus.SUCCEEDED)
        self.assertEqual([record.kind for record in decisions], [DecisionKind.SYSTEM])

    def test_autonomy_queue_pause_state_persists_across_api_requests(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "console.db"
            action = AutonomyActionStore(db_path).create(
                scenario_id="demo-quant",
                proposal_id="proposal-1",
                action_type="prompt_patch",
                checkpoint_id="checkpoint-1",
                reason="Historical shadow passed and patch is low-risk.",
            )
            client, token = self._client(db_path)
            headers = self._auth(token)

            paused = client.post("/api/autonomy/queue/pause", headers=headers)
            status = client.get("/api/autonomy/queue/status", headers=headers)
            blocked_process = client.post(f"/api/autonomy/actions/{action.id}/process", headers=headers)
            still_pending = AutonomyActionStore(db_path).get(action.id)
            resumed = client.post("/api/autonomy/queue/resume", headers=headers)
            resumed_status = client.get("/api/autonomy/queue/status", headers=headers)

        self.assertEqual(paused.status_code, 200)
        self.assertTrue(paused.json()["paused"])
        self.assertEqual(status.status_code, 200)
        self.assertTrue(status.json()["paused"])
        self.assertEqual(blocked_process.status_code, 200)
        self.assertTrue(blocked_process.json()["paused"])
        self.assertIsNotNone(still_pending)
        assert still_pending is not None
        self.assertEqual(still_pending.status, AutonomyActionStatus.PENDING)
        self.assertEqual(resumed.status_code, 200)
        self.assertFalse(resumed.json()["paused"])
        self.assertFalse(resumed_status.json()["paused"])

    def test_autonomy_action_status_filter_rejects_unknown_status_with_error_envelope(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "console.db"
            client, token = self._client(db_path)

            response = client.get(
                "/api/autonomy/actions",
                params={"status": "unknown"},
                headers=self._auth(token),
            )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["code"], "autonomy.invalid_status")
        self.assertEqual(response.json()["details"], {"status": "unknown"})

    @staticmethod
    def _client(db_path: Path) -> tuple[TestClient, str]:
        manager = APIKeyManager()
        token = manager.generate_token("web")
        app = create_app(auth_manager=manager, db_path=db_path, backup_dir=db_path.parent / "backups")
        return TestClient(app), token

    @staticmethod
    def _auth(token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}


if __name__ == "__main__":
    unittest.main()
