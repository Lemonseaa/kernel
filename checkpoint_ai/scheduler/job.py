"""Scheduled job model."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from uuid import uuid4

from checkpoint_ai.models import TaskSpec


class JobType(str, Enum):
    """Supported scheduled job types."""

    INTERVAL = "interval"
    CRON = "cron"


@dataclass(slots=True)
class Job:
    """A scheduled checkpoint_ai workflow."""

    name: str
    job_type: JobType
    task_specs: list[TaskSpec]
    id: str = field(default_factory=lambda: str(uuid4()))
    user_request: str | None = None
    interval_seconds: int | None = None
    cron: str | None = None
    next_run_at: datetime | None = None
    run_count: int = 0
    enabled: bool = True

    def __post_init__(self) -> None:
        """Initialize derived fields and validate schedule configuration."""

        if isinstance(self.job_type, str):
            self.job_type = JobType(self.job_type)
        if self.user_request is None:
            self.user_request = self.name
        if self.next_run_at is None:
            self.next_run_at = self.compute_next_run(datetime.now(timezone.utc))

    def is_due(self, now: datetime | None = None) -> bool:
        """Return whether this job should run now."""

        if not self.enabled or self.next_run_at is None:
            return False
        return self._as_utc(now or datetime.now(timezone.utc)) >= self._as_utc(self.next_run_at)

    def mark_ran(self, now: datetime | None = None) -> None:
        """Record one execution and compute the following run time."""

        current = self._as_utc(now or datetime.now(timezone.utc))
        self.run_count += 1
        self.next_run_at = self.compute_next_run(current)

    def compute_next_run(self, now: datetime | None = None) -> datetime:
        """Compute the next run time after now."""

        current = self._as_utc(now or datetime.now(timezone.utc))
        if self.job_type == JobType.INTERVAL:
            if not self.interval_seconds or self.interval_seconds <= 0:
                raise ValueError("Interval jobs require positive interval_seconds.")
            return current + timedelta(seconds=self.interval_seconds)
        if self.job_type == JobType.CRON:
            return self._compute_cron_next_run(current)
        raise ValueError(f"Unsupported job type: {self.job_type}")

    def _compute_cron_next_run(self, now: datetime) -> datetime:
        """Compute next run for a minimal five-field cron expression."""

        if not self.cron:
            raise ValueError("Cron jobs require cron expression.")
        minute_raw, hour_raw, day_raw, month_raw, weekday_raw = self.cron.split()
        minute = self._parse_cron_value(minute_raw, 0, 59, "minute")
        hour = self._parse_cron_value(hour_raw, 0, 23, "hour")
        day = self._parse_optional_cron_value(day_raw, 1, 31, "day")
        month = self._parse_optional_cron_value(month_raw, 1, 12, "month")
        weekday = self._parse_optional_cron_value(weekday_raw, 0, 6, "weekday")

        candidate = now.replace(second=0, microsecond=0)
        if candidate <= now:
            candidate += timedelta(minutes=1)
        for _ in range(366 * 24 * 60):
            if (
                candidate.minute == minute
                and candidate.hour == hour
                and (day is None or candidate.day == day)
                and (month is None or candidate.month == month)
                and (weekday is None or candidate.weekday() == weekday)
            ):
                return candidate
            candidate += timedelta(minutes=1)
        raise ValueError(f"No next run found for cron: {self.cron}")

    @staticmethod
    def _parse_cron_value(raw: str, minimum: int, maximum: int, label: str) -> int:
        """Parse a required cron field."""

        if raw == "*":
            raise ValueError(f"{label} does not support wildcard in this MVP.")
        value = int(raw)
        if value < minimum or value > maximum:
            raise ValueError(f"{label} out of range: {value}")
        return value

    @staticmethod
    def _parse_optional_cron_value(
        raw: str,
        minimum: int,
        maximum: int,
        label: str,
    ) -> int | None:
        """Parse an optional cron field."""

        if raw == "*":
            return None
        value = int(raw)
        if value < minimum or value > maximum:
            raise ValueError(f"{label} out of range: {value}")
        return value

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        """Ensure datetime values are timezone-aware UTC."""

        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
