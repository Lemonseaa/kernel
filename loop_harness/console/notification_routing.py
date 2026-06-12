"""Notification routing for V5 actionable events."""

from __future__ import annotations

from loop_harness.notification import NotificationManager, NotificationMessage


class NotificationRouter:
    """Route only enabled, human-actionable notification categories."""

    def __init__(
        self,
        notification_manager: NotificationManager,
        enabled_types: set[str] | None = None,
    ) -> None:
        self.notification_manager = notification_manager
        self.enabled_types = enabled_types or {
            "approval_required",
            "budget_warning",
            "adapter_degraded",
            "run_failed",
            "backup_failed",
        }

    def route(self, event_type: str, title: str, body: str, source_id: str) -> bool:
        """Send one notification only when its category is enabled."""

        if event_type not in self.enabled_types:
            return False
        self.notification_manager.notify(
            NotificationMessage(
                title=title,
                body=body,
                type=event_type,
                priority="high" if event_type in {"approval_required", "budget_warning"} else "normal",
                data={"source_id": source_id},
            )
        )
        return True
