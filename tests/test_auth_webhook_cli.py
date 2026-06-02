"""V0.7 auth, webhook, and CLI tests."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from opc_os import OPCOS
from opc_os.api import create_app
from opc_os.auth import APIKeyManager, BearerTokenAuth
from opc_os.events import EventBus, EventType
from opc_os.webhook import WebhookHandler, WebhookReceiver, WebhookSender


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

    def test_opc_os_configure_webhooks_sends_supported_events(self) -> None:
        attempts: list[dict[str, object]] = []

        def transport(url: str, payload: dict[str, object], headers: dict[str, str]) -> object:
            attempts.append({"url": url, "payload": payload, "headers": headers})
            return {"status": 200}

        opc_os = OPCOS()
        sender = opc_os.configure_webhooks(
            ["https://example.test/webhook"],
            transport=transport,
        )

        opc_os.event_bus.emit(EventType.RUN_COMPLETED, {"run_id": "run-1", "state": "succeeded"})

        self.assertIs(opc_os.webhook_sender, sender)
        self.assertEqual(attempts[0]["payload"]["event_type"], "run.completed")

    def test_webhook_receiver_can_trigger_workflow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            opc_os = OPCOS(sqlite_path=Path(tmp) / "opc_os.db")
            handler = WebhookHandler(opc_os)
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
            self.assertEqual(opc_os.store.list_runs()[0]["user_request"], "external workflow")

    def test_cli_status_run_list_business_line_list_and_health(self) -> None:
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "opc_os.db"
            opc_os = OPCOS(sqlite_path=db_path)
            run = opc_os.create_run("cli run")
            opc_os.create_business_line("cli business")
            opc_os.store.save_run(run)

            commands = [
                ["./opc-os", "--db", str(db_path), "status"],
                ["./opc-os", "--db", str(db_path), "run", "list"],
                ["./opc-os", "--db", str(db_path), "bl", "list"],
                ["./opc-os", "--db", str(db_path), "health"],
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
