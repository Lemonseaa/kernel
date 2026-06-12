"""Notification system exports.

Notifications should only route human-actionable events. Do not expand this
into a generic campaign, chat, or alerting platform.
"""

from loop_harness.notification.base import (
    NotificationChannel,
    NotificationDelivery,
    NotificationMessage,
)
from loop_harness.notification.channels import (
    ConsoleNotificationChannel,
    EmailNotificationChannel,
    WebhookNotificationChannel,
)
from loop_harness.notification.manager import NotificationManager

CLEANUP_STATUS = "isolate"
REPLACEMENT_PATH = "human-actionable notification routing"

__all__ = [
    "ConsoleNotificationChannel",
    "EmailNotificationChannel",
    "NotificationChannel",
    "NotificationDelivery",
    "NotificationManager",
    "NotificationMessage",
    "WebhookNotificationChannel",
]
