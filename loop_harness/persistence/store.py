"""Storage abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from loop_harness.businessline.models import BusinessLine, BusinessLineStatus
from loop_harness.models import Run, Task


class Storage(ABC):
    """Persistence interface for run and task state."""

    @abstractmethod
    def save_run(self, run: Run) -> None:
        """Persist a run."""

    @abstractmethod
    def save_task(self, task: Task) -> None:
        """Persist a task."""

    @abstractmethod
    def save_business_line(self, business_line: BusinessLine) -> None:
        """Persist a BusinessLine."""

    @abstractmethod
    def load_business_line(self, business_line_id: str) -> BusinessLine:
        """Load a BusinessLine by id."""

    @abstractmethod
    def list_business_lines(self, status: BusinessLineStatus | None = None) -> list[BusinessLine]:
        """List persisted BusinessLines."""

    @abstractmethod
    def load_run(self, run_id: str) -> dict[str, Any]:
        """Load a run by id."""

    @abstractmethod
    def load_task(self, task_id: str) -> dict[str, Any]:
        """Load a task by id."""

    @abstractmethod
    def list_runs(self, business_line_id: str | None = None) -> list[dict[str, Any]]:
        """List persisted runs, optionally filtered by BusinessLine."""

    @abstractmethod
    def list_tasks(
        self,
        run_id: str | None = None,
        business_line_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """List persisted tasks, optionally filtered by run or BusinessLine."""
