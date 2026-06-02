"""Alert rule models."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable
from uuid import uuid4


class AlertSeverity(str, Enum):
    """Supported alert severities."""

    WARNING = "warning"
    CRITICAL = "critical"


@dataclass(slots=True)
class AlertRule:
    """A runtime event rule that may trigger an alert."""

    id: str
    event_type: str
    severity: AlertSeverity
    description: str
    predicate: Callable[[dict[str, Any]], bool] = lambda _payload: True

    def matches(self, event_type: str, payload: dict[str, Any]) -> bool:
        """Return true when this rule applies to an event."""

        return self.event_type == event_type and self.predicate(payload)


@dataclass(slots=True)
class Alert:
    """A triggered alert."""

    rule_id: str
    severity: AlertSeverity
    message: str
    payload: dict[str, Any]
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: float = field(default_factory=time.time)
