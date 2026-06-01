"""Memory stores for task context."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Any

from kernel.persistence import SQLiteStore


class Memory(ABC):
    """Abstract memory interface."""

    @abstractmethod
    def add(self, run_id: str, task_id: str, content: Any) -> None:
        """Add one memory item."""

    @abstractmethod
    def get_context(self, run_id: str) -> list[dict[str, Any]]:
        """Return context items for one run."""


class WorkingMemory(Memory):
    """Short-term in-memory context."""

    def __init__(self, max_items: int = 20) -> None:
        """Create working memory."""

        self.max_items = max_items
        self._items: dict[str, list[dict[str, Any]]] = defaultdict(list)

    def add(self, run_id: str, task_id: str, content: Any) -> None:
        """Add one context item."""

        items = self._items[run_id]
        items.append({"run_id": run_id, "task_id": task_id, "content": content})
        if len(items) > self.max_items:
            del items[: len(items) - self.max_items]

    def get_context(self, run_id: str) -> list[dict[str, Any]]:
        """Return recent context for one run."""

        return list(self._items.get(run_id, []))


class PersistentMemory(Memory):
    """Long-term memory backed by SQLiteStore."""

    def __init__(self, store: SQLiteStore) -> None:
        """Create persistent memory."""

        self.store = store

    def add(self, run_id: str, task_id: str, content: Any) -> None:
        """Persist one context item."""

        self.store.save_memory(run_id=run_id, task_id=task_id, content=content)

    def get_context(self, run_id: str) -> list[dict[str, Any]]:
        """Load persisted context for one run."""

        return self.store.list_memory(run_id)
