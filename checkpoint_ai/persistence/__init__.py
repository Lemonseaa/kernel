"""Persistence exports.

Persistence is shared support for evidence and compatibility stores. Keep it
small; use external databases or workflow systems for platform-scale needs.
"""

from checkpoint_ai.persistence.sqlite import SQLiteStore
from checkpoint_ai.persistence.store import Storage

CLEANUP_STATUS = "evidence_support"
REPLACEMENT_PATH = "small local persistence utilities"

__all__ = ["SQLiteStore", "Storage"]
