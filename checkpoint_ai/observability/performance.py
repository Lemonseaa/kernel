"""Runtime performance monitoring."""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean

from checkpoint_ai.events import EventBus


@dataclass(slots=True)
class TaskTiming:
    """Execution timing for one task."""

    task_id: str
    duration_seconds: float
    agent: str = ""
    run_id: str = ""


@dataclass(slots=True)
class ProviderTiming:
    """Response timing for one provider call."""

    provider: str
    model: str
    duration_seconds: float


@dataclass(slots=True)
class PerformanceReport:
    """Aggregated performance report."""

    task_count: int
    provider_call_count: int
    average_task_duration_seconds: float
    slow_tasks: list[TaskTiming] = field(default_factory=list)
    provider_average_durations: dict[str, float] = field(default_factory=dict)


class PerformanceMonitor:
    """Collect task and provider timings and emit slow-task events."""

    def __init__(
        self,
        slow_task_threshold_seconds: float = 5.0,
        event_bus: EventBus | None = None,
    ) -> None:
        """Create a performance monitor."""

        self.slow_task_threshold_seconds = slow_task_threshold_seconds
        self.event_bus = event_bus
        self.task_timings: list[TaskTiming] = []
        self.provider_timings: list[ProviderTiming] = []
        self.slow_tasks: list[TaskTiming] = []

    def record_task(
        self,
        task_id: str,
        duration_seconds: float,
        agent: str = "",
        run_id: str = "",
    ) -> None:
        """Record one task duration."""

        timing = TaskTiming(
            task_id=task_id,
            duration_seconds=duration_seconds,
            agent=agent,
            run_id=run_id,
        )
        self.task_timings.append(timing)
        if duration_seconds >= self.slow_task_threshold_seconds:
            self.slow_tasks.append(timing)
            if self.event_bus is not None:
                self.event_bus.emit(
                    "performance:slow_task",
                    {
                        "task_id": task_id,
                        "run_id": run_id,
                        "agent": agent,
                        "duration_seconds": duration_seconds,
                        "threshold_seconds": self.slow_task_threshold_seconds,
                    },
                )

    def record_provider(self, provider: str, model: str, duration_seconds: float) -> None:
        """Record one provider call duration."""

        self.provider_timings.append(
            ProviderTiming(provider=provider, model=model, duration_seconds=duration_seconds)
        )

    def report(self) -> dict[str, object]:
        """Return an aggregated performance report as plain data."""

        provider_groups: dict[str, list[float]] = {}
        for timing in self.provider_timings:
            key = f"{timing.provider}:{timing.model}"
            provider_groups.setdefault(key, []).append(timing.duration_seconds)
        provider_average_durations = {
            key: mean(durations) for key, durations in provider_groups.items()
        }
        average_task_duration = (
            mean(timing.duration_seconds for timing in self.task_timings)
            if self.task_timings
            else 0.0
        )
        return {
            "task_count": len(self.task_timings),
            "provider_call_count": len(self.provider_timings),
            "average_task_duration_seconds": average_task_duration,
            "slow_task_count": len(self.slow_tasks),
            "slow_tasks": [
                {
                    "task_id": timing.task_id,
                    "run_id": timing.run_id,
                    "agent": timing.agent,
                    "duration_seconds": timing.duration_seconds,
                }
                for timing in self.slow_tasks
            ],
            "provider_average_durations": provider_average_durations,
        }
