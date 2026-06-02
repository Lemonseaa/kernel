"""Alert manager."""

from __future__ import annotations

import time
from typing import Any

from kernel.alerts.alert_channel import AlertChannel
from kernel.alerts.alert_rule import Alert, AlertRule, AlertSeverity
from kernel.control import ApprovalState, HumanApprovalGate
from kernel.events import Event, EventBus, EventType
from kernel.notification import NotificationManager


class AlertManager:
    """Evaluate runtime events and send actionable alerts."""

    def __init__(self, event_bus: EventBus, notification_manager: NotificationManager) -> None:
        """Create alert manager and subscribe to runtime events."""

        self.event_bus = event_bus
        self.notification_manager = notification_manager
        self.channel = AlertChannel(notification_manager)
        self.alerts: list[Alert] = []
        self.rules = self._default_rules()
        self._approval_timeout_alerted: set[str] = set()
        self._subscribe()

    def check_rule(self, event: dict[str, Any]) -> bool:
        """Return whether an event triggers any alert rule."""

        event_type = str(event.get("type", ""))
        payload = dict(event.get("payload", {}))
        return any(rule.matches(event_type, payload) for rule in self.rules)

    def trigger_alert(self, rule: AlertRule, event: dict[str, Any]) -> Alert:
        """Trigger one alert and send it through notifications."""

        payload = dict(event.get("payload", {}))
        alert = Alert(
            rule_id=rule.id,
            severity=rule.severity,
            message=self._message_for(rule, payload),
            payload=payload,
        )
        self.alerts.append(alert)
        self.channel.send(alert)
        self.event_bus.emit(
            "alert:triggered",
            {
                "alert_id": alert.id,
                "rule_id": alert.rule_id,
                "severity": alert.severity.value,
            },
        )
        return alert

    def check_approval_timeouts(
        self,
        gate: HumanApprovalGate,
        timeout_seconds: float = 30 * 60,
    ) -> list[Alert]:
        """Check pending approvals and alert when they have waited too long."""

        triggered: list[Alert] = []
        now = time.time()
        rule = self._rule("approval_timeout")
        for request in gate.requests:
            created_at = getattr(request, "created_at", now)
            if (
                request.state == ApprovalState.REQUESTED
                and now - created_at >= timeout_seconds
                and request.id not in self._approval_timeout_alerted
            ):
                self._approval_timeout_alerted.add(request.id)
                triggered.append(
                    self.trigger_alert(
                        rule,
                        {
                            "type": "approval:timeout",
                            "payload": {
                                "approval_id": request.id,
                                "age_seconds": now - created_at,
                                "message": request.message,
                            },
                        },
                    )
                )
        return triggered

    def _subscribe(self) -> None:
        """Subscribe handlers to event bus events."""

        for event_type in {
            EventType.TASK_FAILED.value,
            EventType.RUN_COMPLETED.value,
            "cost.updated",
            "cost.budget_exceeded",
            "provider:error",
            "performance:slow_task",
        }:
            self.event_bus.subscribe(event_type, self._handle_event)

    def _handle_event(self, event: Event) -> None:
        """Evaluate one emitted event."""

        event_dict = {"type": event.type, "payload": event.payload}
        for rule in self.rules:
            if rule.matches(event.type, event.payload):
                self.trigger_alert(rule, event_dict)

    def _default_rules(self) -> list[AlertRule]:
        """Return built-in OPC alert rules."""

        return [
            AlertRule(
                id="task_failed",
                event_type=EventType.TASK_FAILED.value,
                severity=AlertSeverity.WARNING,
                description="Task failed.",
            ),
            AlertRule(
                id="run_failed",
                event_type=EventType.RUN_COMPLETED.value,
                severity=AlertSeverity.WARNING,
                description="Run failed.",
                predicate=lambda payload: payload.get("state") == "failed",
            ),
            AlertRule(
                id="cost_budget_warning",
                event_type="cost.updated",
                severity=AlertSeverity.WARNING,
                description="Cost reached 80% of budget.",
                predicate=self._cost_at_least(0.8, below=0.95),
            ),
            AlertRule(
                id="cost_budget_critical",
                event_type="cost.updated",
                severity=AlertSeverity.CRITICAL,
                description="Cost reached 95% of budget.",
                predicate=self._cost_at_least(0.95, below=1.0),
            ),
            AlertRule(
                id="cost_budget_exceeded",
                event_type="cost.budget_exceeded",
                severity=AlertSeverity.CRITICAL,
                description="Cost exceeded budget.",
            ),
            AlertRule(
                id="approval_timeout",
                event_type="approval:timeout",
                severity=AlertSeverity.WARNING,
                description="Approval request has waited too long.",
            ),
            AlertRule(
                id="provider_error",
                event_type="provider:error",
                severity=AlertSeverity.CRITICAL,
                description="Provider call failed.",
            ),
            AlertRule(
                id="slow_task",
                event_type="performance:slow_task",
                severity=AlertSeverity.WARNING,
                description="Task execution exceeded slow-task threshold.",
            ),
        ]

    def _cost_at_least(self, threshold: float, below: float | None = None):
        """Build a budget-ratio predicate."""

        def predicate(payload: dict[str, Any]) -> bool:
            budget = payload.get("budget")
            current = payload.get("current")
            if not isinstance(budget, (int, float)) or not isinstance(current, (int, float)):
                return False
            if budget <= 0:
                return False
            ratio = current / budget
            if below is not None and ratio >= below:
                return False
            return ratio >= threshold

        return predicate

    def _rule(self, rule_id: str) -> AlertRule:
        """Return a rule by id."""

        for rule in self.rules:
            if rule.id == rule_id:
                return rule
        raise KeyError(f"Alert rule not found: {rule_id}")

    def _message_for(self, rule: AlertRule, payload: dict[str, Any]) -> str:
        """Build a concise alert message."""

        if rule.id.startswith("cost_budget"):
            return (
                f"{rule.description} provider={payload.get('provider')} "
                f"business_line={payload.get('business_line_id')} "
                f"current={payload.get('current')} budget={payload.get('budget')}"
            )
        if rule.id == "task_failed":
            return f"Task failed: {payload.get('task_id')} error={payload.get('error', '')}"
        if rule.id == "run_failed":
            return f"Run failed: {payload.get('run_id')}"
        if rule.id == "approval_timeout":
            return f"Approval timed out: {payload.get('approval_id')}"
        if rule.id == "provider_error":
            return f"Provider error: {payload.get('provider')} error={payload.get('error', '')}"
        if rule.id == "slow_task":
            return (
                f"Slow task: {payload.get('task_id')} "
                f"duration={payload.get('duration_seconds')}s "
                f"threshold={payload.get('threshold_seconds')}s"
            )
        return rule.description
