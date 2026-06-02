"""Performance observability tests."""

from __future__ import annotations

import unittest

from opc_os.events import EventBus
from opc_os.observability import PerformanceMonitor


class PerformanceMonitorTest(unittest.TestCase):
    """Validate runtime performance monitoring."""

    def test_records_task_and_provider_timings(self) -> None:
        monitor = PerformanceMonitor(slow_task_threshold_seconds=10.0)

        monitor.record_task(task_id="task-1", duration_seconds=1.5, agent="writer")
        monitor.record_provider(provider="minimax", model="m1", duration_seconds=0.25)

        report = monitor.report()
        self.assertEqual(report["task_count"], 1)
        self.assertEqual(report["provider_call_count"], 1)
        self.assertEqual(report["average_task_duration_seconds"], 1.5)
        self.assertEqual(report["provider_average_durations"]["minimax:m1"], 0.25)

    def test_slow_task_emits_alert_event(self) -> None:
        bus = EventBus()
        monitor = PerformanceMonitor(slow_task_threshold_seconds=0.5, event_bus=bus)

        monitor.record_task(task_id="task-1", duration_seconds=0.75, agent="writer", run_id="run-1")

        self.assertEqual(len(monitor.slow_tasks), 1)
        self.assertIn("performance:slow_task", [event.type for event in bus.events])


if __name__ == "__main__":
    unittest.main()
