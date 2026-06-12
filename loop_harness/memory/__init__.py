"""Memory and context exports.

Memory is legacy runtime support. Future evidence work should prefer explicit
logs, traces, reports, and user-owned profiles over vague long-term memory.
"""

from loop_harness.memory.context import ContextManager
from loop_harness.memory.memory import Memory, PersistentMemory, WorkingMemory

CLEANUP_STATUS = "isolate"
REPLACEMENT_PATH = "explicit evidence logs and user profile"

__all__ = ["ContextManager", "Memory", "PersistentMemory", "WorkingMemory"]
