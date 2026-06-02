"""Alert channel adapters."""

from __future__ import annotations

from dataclasses import dataclass

from kernel.alerts.alert_rule import Alert
from kernel.notification import NotificationDelivery, NotificationManager, NotificationMessage


@dataclass(slots=True)
class AlertChannel:
    """Send alerts through the existing notification manager."""

    notification_manager: NotificationManager

    def send(self, alert: Alert) -> list[NotificationDelivery]:
        """Send one alert as a notification."""

        message = NotificationMessage(
            title=f"系统告警: {alert.rule_id}",
            body=alert.message,
            type="alert",
            priority="high" if alert.severity.value == "critical" else "normal",
            data={
                "alert_id": alert.id,
                "rule_id": alert.rule_id,
                "severity": alert.severity.value,
                **alert.payload,
            },
        )
        return self.notification_manager.notify(message)
