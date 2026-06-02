"""Runtime cost tracking tests."""

from __future__ import annotations

import unittest
from datetime import date

from checkpoint_ai.control import HumanApprovalGate
from checkpoint_ai.events import EventBus
from checkpoint_ai.observability import CostTracker


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

    def test_human_gate_creates_request_for_budget_exceeded_event(self) -> None:
        bus = EventBus()
        gate = HumanApprovalGate(auto_approve=None, event_bus=bus)
        gate.subscribe_to_cost_events()
        tracker = CostTracker(event_bus=bus)
        tracker.set_budget("minimax", daily_budget=1.0, business_line_id="bl-a")

        tracker.track("minimax", 800, 400, business_line_id="bl-a")

        self.assertEqual(len(gate.pending_requests()), 1)
        request = gate.pending_requests()[0]
        self.assertEqual(request.policy.action, "cost.budget_exceeded")
        self.assertEqual(request.subject["business_line_id"], "bl-a")

    def test_daily_budget_resets_by_date_and_keeps_period_reports(self) -> None:
        current_day = date(2026, 6, 2)
        tracker = CostTracker(today_provider=lambda: current_day)

        tracker.track("minimax", 100, 100, business_line_id="bl-a")
        current_day = date(2026, 6, 3)
        tracker.track("minimax", 200, 100, business_line_id="bl-a")

        self.assertEqual(
            tracker.get_daily_cost("minimax", business_line_id="bl-a", day=date(2026, 6, 2)).total_tokens,
            200,
        )
        self.assertEqual(
            tracker.get_daily_cost("minimax", business_line_id="bl-a", day=date(2026, 6, 3)).total_tokens,
            300,
        )
        self.assertEqual(
            tracker.report_period(
                start=date(2026, 6, 2),
                end=date(2026, 6, 3),
                business_line_id="bl-a",
            ).total_tokens,
            500,
        )

    def test_budget_warning_publishes_at_eighty_percent_once_per_day(self) -> None:
        current_day = date(2026, 6, 2)
        bus = EventBus()
        warnings = []
        bus.subscribe("cost.budget_warning", lambda event: warnings.append(event))
        tracker = CostTracker(event_bus=bus, today_provider=lambda: current_day)
        tracker.set_budget("minimax", daily_budget=1.0, business_line_id="bl-a")

        tracker.track("minimax", 500, 300, business_line_id="bl-a")
        tracker.track("minimax", 10, 10, business_line_id="bl-a")
        current_day = date(2026, 6, 3)
        tracker.track("minimax", 800, 0, business_line_id="bl-a")

        self.assertEqual(len(warnings), 2)
        self.assertEqual(warnings[0].payload["threshold"], 0.8)
        self.assertEqual(warnings[0].payload["day"], "2026-06-02")
        self.assertEqual(warnings[1].payload["day"], "2026-06-03")


if __name__ == "__main__":
    unittest.main()
