"""Kernel metrics collection."""

from __future__ import annotations

from dataclasses import dataclass, field
from time import monotonic
from typing import Any

from opc_os.events import Event, EventType


@dataclass(slots=True)
class MetricsCollector:
    """Collect lightweight in-memory kernel metrics."""

    run_count: int = 0
    run_completed: int = 0
    task_count: int = 0
    task_success: int = 0
    task_failed: int = 0
    total_latency: float = 0.0
    _run_started_at: dict[str, float] = field(default_factory=dict)

    def record(self, event: Event) -> None:
        """Update metrics from an emitted event."""

        if event.type == EventType.RUN_STARTED.value:
            run_id = str(event.payload.get("run_id", ""))
            self.run_count += 1
            if run_id:
                self._run_started_at[run_id] = monotonic()
            return
        if event.type == EventType.RUN_COMPLETED.value:
            self.run_completed += 1
            run_id = str(event.payload.get("run_id", ""))
            started_at = self._run_started_at.pop(run_id, None)
            if started_at is not None:
                self.total_latency += monotonic() - started_at
            return
        if event.type == EventType.TASK_COMPLETED.value:
            self.task_count += 1
            self.task_success += 1
            return
        if event.type == EventType.TASK_FAILED.value:
            self.task_count += 1
            self.task_failed += 1

    def get_summary(self) -> dict[str, Any]:
        """Return a metrics snapshot."""

        success_rate = self.task_success / self.task_count if self.task_count else 0.0
        average_latency = self.total_latency / self.run_completed if self.run_completed else 0.0
        return {
            "run_count": self.run_count,
            "run_completed": self.run_completed,
            "task_count": self.task_count,
            "task_success": self.task_success,
            "task_failed": self.task_failed,
            "success_rate": success_rate,
            "total_latency": self.total_latency,
            "average_latency": average_latency,
        }
