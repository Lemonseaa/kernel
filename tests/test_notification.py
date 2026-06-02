"""Notification system tests."""

from __future__ import annotations

import io
import unittest
from contextlib import redirect_stdout

from opc_os.cli import main
from opc_os.control import HumanApprovalGate, PolicyEngine
from opc_os.models import Task
from opc_os.notification import (
    NotificationChannel,
    NotificationDelivery,
    NotificationManager,
    NotificationMessage,
    WebhookNotificationChannel,
)


class RecordingChannel(NotificationChannel):
    """Test channel that records outgoing messages."""

    name = "recording"

    def __init__(self) -> None:
        """Create an empty recording channel."""

        self.messages: list[NotificationMessage] = []

    def send(self, message: NotificationMessage) -> NotificationDelivery:
        """Record one message."""

        self.messages.append(message)
        return NotificationDelivery(channel=self.name, success=True)


class NotificationTest(unittest.TestCase):
    """Validate notification channels and kernel integrations."""

    def test_notification_manager_sends_to_registered_channels(self) -> None:
        manager = NotificationManager()
        channel = RecordingChannel()
        manager.register(channel)

        deliveries = manager.notify(NotificationMessage(title="需要审批", body="任务等待处理"))

        self.assertEqual(len(deliveries), 1)
        self.assertTrue(deliveries[0].success)
        self.assertEqual(channel.messages[0].title, "需要审批")
        self.assertEqual(len(manager.history), 1)

    def test_webhook_channel_uses_injected_transport(self) -> None:
        calls: list[dict[str, object]] = []

        def transport(url: str, payload: dict[str, object], headers: dict[str, str]) -> dict[str, object]:
            calls.append({"url": url, "payload": payload, "headers": headers})
            return {"status": 202}

        channel = WebhookNotificationChannel("https://example.invalid/hook", transport=transport)
        delivery = channel.send(NotificationMessage(title="告警", body="需要处理", type="alert"))

        self.assertTrue(delivery.success)
        self.assertEqual(calls[0]["url"], "https://example.invalid/hook")
        self.assertEqual(calls[0]["payload"]["title"], "告警")

    def test_human_gate_notifies_when_approval_is_requested(self) -> None:
        manager = NotificationManager()
        channel = RecordingChannel()
        manager.register(channel)
        gate = HumanApprovalGate(auto_approve=None, notification_manager=manager)
        policy = PolicyEngine(high_risk_keywords={"publish"}).evaluate_action("publish content")
        task = Task(name="publish content", agent_capability="simple.execute")

        gate.request_approval(policy, message="Task needs approval", subject=task)

        self.assertEqual(len(channel.messages), 1)
        self.assertEqual(channel.messages[0].type, "approval_required")
        self.assertEqual(channel.messages[0].data["task_id"], task.id)

    def test_cli_can_send_console_notification(self) -> None:
        stdout = io.StringIO()

        with redirect_stdout(stdout):
            exit_code = main(["notify", "--title", "测试通知", "--body", "需要处理"])

        self.assertEqual(exit_code, 0)
        self.assertIn("测试通知", stdout.getvalue())
