"""Notification channel abstractions."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass(slots=True)
class NotificationMessage:
    """A notification payload sent to humans or external systems."""

    title: str
    body: str
    type: str = "info"
    priority: str = "normal"
    data: dict[str, Any] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        """Serialize the message for transports."""

        return {
            "id": self.id,
            "title": self.title,
            "body": self.body,
            "type": self.type,
            "priority": self.priority,
            "data": self.data,
            "created_at": self.created_at,
        }


@dataclass(slots=True)
class NotificationDelivery:
    """Delivery result for one notification channel."""

    channel: str
    success: bool
    message_id: str | None = None
    error: str | None = None


class NotificationChannel(ABC):
    """Base class for notification channels."""

    name: str = "base"

    @abstractmethod
    def send(self, message: NotificationMessage) -> NotificationDelivery:
        """Send a notification message."""
