"""checkpointAI workflow scheduler."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from typing import Any

from checkpoint_ai.scheduler.job import Job


class Scheduler:
    """In-memory scheduler for interval and cron jobs."""

    def __init__(self, now: Callable[[], datetime] | None = None) -> None:
        """Create a scheduler."""

        self._now = now or (lambda: datetime.now(timezone.utc))
        self._jobs: dict[str, Job] = {}

    def add_job(self, job: Job) -> Job:
        """Register a scheduled job."""

        self._jobs[job.id] = job
        return job

    def remove_job(self, job_id: str) -> bool:
        """Remove a scheduled job by id."""

        return self._jobs.pop(job_id, None) is not None

    def list_jobs(self) -> list[Job]:
        """List scheduled jobs."""

        return list(self._jobs.values())

    def due_jobs(self, now: datetime | None = None) -> list[Job]:
        """Return jobs due at the given time."""

        current = now or self._now()
        return [job for job in self._jobs.values() if job.is_due(current)]

    def run_due(self, handler: Callable[[Job], Any], now: datetime | None = None) -> int:
        """Run all currently due jobs through a handler."""

        current = now or self._now()
        due = self.due_jobs(current)
        for job in due:
            handler(job)
            job.mark_ran(current)
        return len(due)
