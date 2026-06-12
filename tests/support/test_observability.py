"""Observability and persistence tests."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from checkpoint_ai.events import AuditLogger, Event, EventType
from checkpoint_ai.observability import MetricsCollector


class ObservabilityTest(unittest.TestCase):
    """Validate audit log and metrics behavior."""

    def test_audit_logger_writes_json_lines(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            log_path = Path(tmp) / "audit.jsonl"
            logger = AuditLogger(path=log_path)
            event = Event(
                type=EventType.TASK_COMPLETED.value,
                payload={"run_id": "run-1", "task_id": "task-1", "agent": "simple"},
            )

            logger.log(event)

            self.assertEqual(len(logger.records), 1)
            row = json.loads(log_path.read_text(encoding="utf-8").strip())
            self.assertEqual(row["event_type"], "task:completed")
            self.assertEqual(row["run_id"], "run-1")
            self.assertEqual(row["task_id"], "task-1")
            self.assertEqual(row["agent_name"], "simple")

    def test_metrics_collector_tracks_task_and_run_events(self) -> None:
        metrics = MetricsCollector()

        metrics.record(Event(type=EventType.RUN_STARTED.value, payload={"run_id": "run-1"}))
        metrics.record(Event(type=EventType.TASK_COMPLETED.value, payload={"task_id": "task-1"}))
        metrics.record(Event(type=EventType.TASK_FAILED.value, payload={"task_id": "task-2"}))
        metrics.record(Event(type=EventType.RUN_COMPLETED.value, payload={"run_id": "run-1"}))

        summary = metrics.get_summary()

        self.assertEqual(summary["run_count"], 1)
        self.assertEqual(summary["task_count"], 2)
        self.assertEqual(summary["task_success"], 1)
        self.assertEqual(summary["task_failed"], 1)
        self.assertEqual(summary["success_rate"], 0.5)
