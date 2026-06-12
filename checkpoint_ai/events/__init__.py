"""Event system exports.

Events are support plumbing for audit and evidence flow. They should stay
small and local instead of becoming a distributed message-bus platform.
"""

from checkpoint_ai.events.bus import Event, EventBus, EventType
from checkpoint_ai.events.logger import AuditLogger

CLEANUP_STATUS = "evidence_support"
REPLACEMENT_PATH = "local audit/event plumbing"

__all__ = ["AuditLogger", "Event", "EventBus", "EventType"]
