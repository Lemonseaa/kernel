"""Task queue."""

from __future__ import annotations

from collections import deque

from kernel.models import Task


class TaskQueue:
    """FIFO task queue."""

    def __init__(self) -> None:
        """Create an empty queue."""

        self._items: deque[Task] = deque()

    def push(self, task: Task) -> None:
        """Add a task to the queue."""

        self._items.append(task)

    def pop(self) -> Task | None:
        """Pop the next task."""

        if not self._items:
            return None
        return self._items.popleft()

    def __len__(self) -> int:
        """Return queue length."""

        return len(self._items)
