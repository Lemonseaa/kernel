"""V0.7 auth, webhook, and CLI tests."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from checkpoint_ai import CheckpointAI
from checkpoint_ai.api import create_app
from checkpoint_ai.auth import APIKeyManager, BearerTokenAuth
from checkpoint_ai.events import EventBus, EventType
from checkpoint_ai.webhook import WebhookHandler, WebhookReceiver, WebhookSender
from tests.helpers import project_root


class AuthWebhookCliTest(unittest.TestCase):
    """Validate API auth, webhook integration, and CLI operations."""

    def test_api_key_manager_generates_verifies_and_revokes_tokens(self) -> None:
        manager = APIKeyManager()

        token = manager.generate_token("ops")

        self.assertTrue(manager.verify_token(token))
        self.assertFalse(manager.verify_token("bad-token"))
        self.assertTrue(manager.revoke_token(token))
        self.assertFalse(manager.verify_token(token))

    def test_bearer_auth_requires_valid_authorization_header(self) -> None:
        manager = APIKeyManager()
        token = manager.generate_token("ops")
        auth = BearerTokenAuth(manager)

        self.assertTrue(auth.authenticate(f"Bearer {token}"))
        self.assertFalse(auth.authenticate(""))
        self.assertFalse(auth.authenticate("Bearer invalid"))

    def test_create_app_exposes_auth_for_fallback_or_fastapi(self) -> None:
        manager = APIKeyManager()
        token = manager.generate_token("api")
        app = create_app(auth_manager=manager)

        if hasattr(app, "authenticate"):
            self.assertTrue(app.authenticate(f"Bearer {token}"))
            self.assertFalse(app.authenticate("Bearer invalid"))
        else:
            self.assertTrue(hasattr(app, "dependency_overrides") or hasattr(app, "routes"))

    def test_webhook_sender_subscribes_and_retries_events(self) -> None:
        bus = EventBus()
        attempts: list[dict[str, object]] = []

        def transport(url: str, payload: dict[str, object], headers: dict[str, str]) -> object:
            attempts.append({"url": url, "payload": payload, "headers": headers})
            if len(attempts) == 1:
                raise RuntimeError("temporary")
            return {"status": 200}

        sender = WebhookSender(
            event_bus=bus,
            urls=["https://example.test/webhook"],
            transport=transport,
            max_retries=1,
        )

        bus.emit(EventType.TASK_FAILED, {"task_id": "task-1"})

        self.assertEqual(len(attempts), 2)
        self.assertEqual(len(sender.deliveries), 1)
        self.assertTrue(sender.deliveries[0].success)
        self.assertEqual(attempts[-1]["payload"]["event_type"], "task.failed")

    def test_checkpoint_ai_configure_webhooks_sends_supported_events(self) -> None:
        attempts: list[dict[str, object]] = []

        def transport(url: str, payload: dict[str, object], headers: dict[str, str]) -> object:
            attempts.append({"url": url, "payload": payload, "headers": headers})
            return {"status": 200}

        checkpoint_ai = CheckpointAI()
        sender = checkpoint_ai.configure_webhooks(
            ["https://example.test/webhook"],
            transport=transport,
        )

        checkpoint_ai.event_bus.emit(EventType.RUN_COMPLETED, {"run_id": "run-1", "state": "succeeded"})

        self.assertIs(checkpoint_ai.webhook_sender, sender)
        self.assertEqual(attempts[0]["payload"]["event_type"], "run.completed")

    def test_webhook_receiver_can_trigger_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            checkpoint_ai = CheckpointAI(sqlite_path=Path(tmp) / "checkpoint_ai.db")
            handler = WebhookHandler(checkpoint_ai)
            receiver = WebhookReceiver(handler=handler)

            result = receiver.receive(
                {
                    "event_type": "workflow.trigger",
                    "payload": {
                        "description": "external workflow",
                        "tasks": [{"description": "hello"}],
                    },
                }
            )

            self.assertEqual(result["status"], "accepted")
            self.assertEqual(checkpoint_ai.store.list_runs()[0]["user_request"], "external workflow")

    def test_cli_status_run_list_business_line_list_and_health(self) -> None:
        root = project_root()
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "checkpoint_ai.db"
            checkpoint_ai = CheckpointAI(sqlite_path=db_path)
            run = checkpoint_ai.create_run("cli run")
            checkpoint_ai.create_business_line("cli business")
            checkpoint_ai.store.save_run(run)

            commands = [
                ["./checkpointai", "--db", str(db_path), "status"],
                ["./checkpointai", "--db", str(db_path), "run", "list"],
                ["./checkpointai", "--db", str(db_path), "bl", "list"],
                ["./checkpointai", "--db", str(db_path), "health"],
            ]
            outputs: list[str] = []
            for command in commands:
                result = subprocess.run(
                    command,
                    cwd=root,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                outputs.append(result.stdout)

        self.assertIn("runs", outputs[0])
        self.assertIn("cli run", outputs[1])
        self.assertIn("cli business", outputs[2])
        self.assertIn("overall_status", outputs[3])


if __name__ == "__main__":
    unittest.main()
