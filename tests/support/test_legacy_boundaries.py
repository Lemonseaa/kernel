"""Legacy module boundary tests."""

from __future__ import annotations

import unittest

from loop_harness import (
    adapter,
    auth,
    autonomy,
    businessline,
    console,
    control,
    diagnostics,
    events,
    experiment,
    external_agents,
    insights,
    isolation,
    learning,
    llm,
    logs,
    loop,
    memory,
    notification,
    observability,
    optimization,
    persistence,
    prompt,
    recommendation,
    runtime,
    scenario,
    tools,
    user_profile,
    workflow,
)


class LegacyBoundaryTest(unittest.TestCase):
    """Legacy packages must advertise their cleanup status."""

    def test_frozen_legacy_modules_expose_status(self) -> None:
        """Frozen modules stay import-compatible but are no longer mainline."""
        frozen_modules = [
            external_agents,
            insights,
            runtime,
            workflow,
        ]

        for module in frozen_modules:
            with self.subTest(module=module.__name__):
                self.assertEqual(module.LEGACY_STATUS, "frozen")
                self.assertTrue(module.REPLACEMENT_PATH)

    def test_adapter_is_marked_as_rewrite_transition(self) -> None:
        """The old Agent adapter layer is kept only as a transition surface."""
        self.assertEqual(adapter.LEGACY_STATUS, "rewrite")
        self.assertIn("EvidenceAdapter", adapter.REPLACEMENT_PATH)

    def test_optimization_layer_is_bounded_by_evidence_status(self) -> None:
        """Learning and optimization modules must not become autonomous platforms."""
        expected_status = {
            autonomy: "isolate",
            learning: "rewrite",
            logs: "evidence_support",
            optimization: "isolate",
            prompt: "evidence_support",
            recommendation: "evidence_support",
        }

        for module, status in expected_status.items():
            with self.subTest(module=module.__name__):
                self.assertEqual(module.CLEANUP_STATUS, status)
                self.assertTrue(module.REPLACEMENT_PATH)

    def test_domain_boundary_modules_have_explicit_scope(self) -> None:
        """Domain modules must stay scoped to evidence boundaries and human preferences."""
        expected_status = {
            businessline: "isolate",
            isolation: "evidence_support",
            memory: "isolate",
            scenario: "evidence_support",
            user_profile: "keep",
        }

        for module, status in expected_status.items():
            with self.subTest(module=module.__name__):
                self.assertEqual(module.CLEANUP_STATUS, status)
                self.assertTrue(module.REPLACEMENT_PATH)

    def test_support_modules_are_bounded_not_platforms(self) -> None:
        """Support modules can remain, but must advertise their limited scope."""
        expected_status = {
            auth: "isolate",
            console: "evidence_support",
            control: "isolate",
            diagnostics: "evidence_support",
            events: "evidence_support",
            experiment: "evidence_support",
            llm: "isolate",
            loop: "evidence_support",
            notification: "isolate",
            observability: "evidence_support",
            persistence: "evidence_support",
            tools: "isolate",
        }

        for module, status in expected_status.items():
            with self.subTest(module=module.__name__):
                self.assertEqual(module.CLEANUP_STATUS, status)
                self.assertTrue(module.REPLACEMENT_PATH)


if __name__ == "__main__":
    unittest.main()
