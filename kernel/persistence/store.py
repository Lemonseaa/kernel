"""Storage abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from kernel.models import Run, Task


class Storage(ABC):
    """Persistence interface for run and task state."""

    @abstractmethod
    def save_run(self, run: Run) -> None:
        """Persist a run."""

    @abstractmethod
    def save_task(self, task: Task) -> None:
        """Persist a task."""

    @abstractmethod
    def load_run(self, run_id: str) -> dict[str, Any]:
        """Load a run by id."""

    @abstractmethod
    def load_task(self, task_id: str) -> dict[str, Any]:
        """Load a task by id."""
