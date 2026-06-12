"""Event system exports.

Events are support plumbing for audit and evidence flow. They should stay
small and local instead of becoming a distributed message-bus platform.
"""

from loop_harness.events.bus import Event, EventBus, EventType
from loop_harness.events.logger import AuditLogger

CLEANUP_STATUS = "evidence_support"
REPLACEMENT_PATH = "local audit/event plumbing"

__all__ = ["AuditLogger", "Event", "EventBus", "EventType"]
