"""Task queue."""

from __future__ import annotations

from collections import deque

from kernel.models import Task


class TaskQueue:
    """FIFO task queue."""

    def __init__(self) -> None:
        """Create an empty queue."""

        self._items: deque[Task] = deque()
        self._queued_ids: set[str] = set()

    def push(self, task: Task) -> None:
        """Add a task to the queue."""

        if task.id in self._queued_ids:
            return
        self._items.append(task)
        self._queued_ids.add(task.id)

    def pop(self) -> Task | None:
        """Pop the next task."""

        if not self._items:
            return None
        task = self._items.popleft()
        self._queued_ids.discard(task.id)
        return task

    def __len__(self) -> int:
        """Return queue length."""

        return len(self._items)
