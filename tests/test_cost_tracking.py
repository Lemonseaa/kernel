"""Runtime cost tracking tests."""

from __future__ import annotations

import unittest

from kernel.events import EventBus
from kernel.observability import CostTracker


class CostTrackingTest(unittest.TestCase):
    """Validate token cost tracking as runtime events."""

    def test_tracks_tokens_and_publishes_cost_update_events(self) -> None:
        bus = EventBus()
        events = []
        bus.subscribe("cost.updated", lambda event: events.append(event))
        tracker = CostTracker(event_bus=bus)

        tracker.track("minimax", input_tokens=1000, output_tokens=500, business_line_id="bl-a")
        cost = tracker.get_cost("minimax")

        self.assertEqual(cost.provider, "minimax")
        self.assertEqual(cost.input_tokens, 1000)
        self.assertEqual(cost.output_tokens, 500)
        self.assertEqual(cost.total_tokens, 1500)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].payload["provider"], "minimax")
        self.assertEqual(events[0].payload["business_line_id"], "bl-a")

    def test_budget_exceeded_publishes_alert_event(self) -> None:
        bus = EventBus()
        alerts = []
        bus.subscribe("cost.budget_exceeded", lambda event: alerts.append(event))
        tracker = CostTracker(event_bus=bus)
        tracker.set_budget("minimax", daily_budget=1.0)

        tracker.track("minimax", input_tokens=800, output_tokens=400)

        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0].payload["provider"], "minimax")
        self.assertGreater(alerts[0].payload["current"], alerts[0].payload["budget"])

    def test_cost_tracker_can_scope_counters_by_business_line(self) -> None:
        tracker = CostTracker()

        tracker.track("minimax", 100, 50, business_line_id="bl-a")
        tracker.track("minimax", 200, 100, business_line_id="bl-b")

        self.assertEqual(tracker.get_cost("minimax", business_line_id="bl-a").total_tokens, 150)
        self.assertEqual(tracker.get_cost("minimax", business_line_id="bl-b").total_tokens, 300)


if __name__ == "__main__":
    unittest.main()
