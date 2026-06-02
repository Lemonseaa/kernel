"""Scheduler tests."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from checkpoint_ai import CheckpointAI
from checkpoint_ai.models import TaskSpec
from checkpoint_ai.scheduler import Job, JobType, Scheduler


class SchedulerTest(unittest.TestCase):
    """Validate interval, cron, checkpoint_ai integration, and CLI scheduling."""

    def test_interval_job_runs_when_due(self) -> None:
        calls = []
        scheduler = Scheduler(now=lambda: datetime(2026, 1, 1, tzinfo=timezone.utc))
        job = Job(
            name="daily hello",
            job_type=JobType.INTERVAL,
            task_specs=[TaskSpec(description="hello")],
            interval_seconds=60,
            next_run_at=datetime(2025, 12, 31, tzinfo=timezone.utc),
        )

        scheduler.add_job(job)
        due = scheduler.run_due(lambda due_job: calls.append(due_job.name))

        self.assertEqual(due, 1)
        self.assertEqual(calls, ["daily hello"])
        self.assertEqual(job.run_count, 1)
        self.assertEqual(job.next_run_at, datetime(2026, 1, 1, 0, 1, tzinfo=timezone.utc))

    def test_cron_daily_job_computes_next_run(self) -> None:
        job = Job(
            name="daily work",
            job_type=JobType.CRON,
            task_specs=[TaskSpec(description="work")],
            cron="30 9 * * *",
        )
        now = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)

        next_run = job.compute_next_run(now)

        self.assertEqual(next_run, datetime(2026, 1, 1, 9, 30, tzinfo=timezone.utc))

    def test_checkpoint_ai_schedule_registers_job_and_cli_lists(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "checkpoint_ai.db"
            checkpoint_ai = CheckpointAI(sqlite_path=db_path)

            job = checkpoint_ai.schedule(
                name="daily report",
                tasks=[TaskSpec(description="report")],
                interval_seconds=3600,
            )

            self.assertEqual(checkpoint_ai.scheduler.list_jobs()[0].id, job.id)

        result = subprocess.run(
            [sys.executable, "-m", "checkpoint_ai.cli", "schedule", "list"],
            cwd=Path(__file__).resolve().parents[1],
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("No scheduled jobs", result.stdout)
