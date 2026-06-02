"""Alert system tests."""

from __future__ import annotations

import time
import unittest

from kernel.alerts import AlertManager, AlertSeverity
from kernel.control import HumanApprovalGate, PolicyDecision, PolicyEvaluation
from kernel.events import EventBus, EventType
from kernel.notification import NotificationManager
from kernel.observability import CostTracker


class AlertSystemTest(unittest.TestCase):
    """Validate alert rules and notification fanout."""

    def test_task_failed_event_triggers_warning_alert(self) -> None:
        bus = EventBus()
        notifications = NotificationManager()
        manager = AlertManager(bus, notifications)

        bus.emit(EventType.TASK_FAILED, {"task_id": "task-1", "error": "boom"})

        self.assertEqual(len(manager.alerts), 1)
        self.assertEqual(manager.alerts[0].rule_id, "task_failed")
        self.assertEqual(manager.alerts[0].severity, AlertSeverity.WARNING)
        self.assertEqual(notifications.history[-1].type, "alert")

    def test_cost_thresholds_trigger_warning_and_critical_alerts(self) -> None:
        bus = EventBus()
        notifications = NotificationManager()
        manager = AlertManager(bus, notifications)
        tracker = CostTracker(event_bus=bus)
        tracker.set_budget("minimax", daily_budget=1.0, business_line_id="bl-a")

        tracker.track("minimax", 800, 0, business_line_id="bl-a")
        tracker.track("minimax", 150, 0, business_line_id="bl-a")

        severities = [alert.severity for alert in manager.alerts]
        self.assertIn(AlertSeverity.WARNING, severities)
        self.assertIn(AlertSeverity.CRITICAL, severities)
        self.assertTrue(any(alert.rule_id == "cost_budget_warning" for alert in manager.alerts))
        self.assertTrue(any(alert.rule_id == "cost_budget_critical" for alert in manager.alerts))

    def test_approval_timeout_triggers_warning_alert(self) -> None:
        bus = EventBus()
        notifications = NotificationManager()
        manager = AlertManager(bus, notifications)
        gate = HumanApprovalGate(auto_approve=None, event_bus=bus)
        request = gate.create_request(
            PolicyEvaluation(
                action="publish",
                decision=PolicyDecision.REVIEW,
                requires_approval=True,
                reason="needs approval",
            )
        )
        request.created_at = time.time() - 31 * 60

        manager.check_approval_timeouts(gate)

        self.assertEqual(manager.alerts[-1].rule_id, "approval_timeout")
        self.assertEqual(manager.alerts[-1].severity, AlertSeverity.WARNING)

    def test_provider_error_event_triggers_critical_alert(self) -> None:
        bus = EventBus()
        notifications = NotificationManager()
        manager = AlertManager(bus, notifications)

        bus.emit("provider:error", {"provider": "minimax", "error": "timeout"})

        self.assertEqual(manager.alerts[-1].rule_id, "provider_error")
        self.assertEqual(manager.alerts[-1].severity, AlertSeverity.CRITICAL)


if __name__ == "__main__":
    unittest.main()
