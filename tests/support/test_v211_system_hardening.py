"""System hardening tests for policy boundaries and scenario ownership."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from checkpoint_ai import CheckpointAI
from checkpoint_ai.policy import ScenarioPolicy
from checkpoint_ai.scenario import Scenario, ScenarioStore


class V211SystemHardeningTest(unittest.TestCase):
    """Lock down relationships that were ambiguous after V2.10."""

    def test_scenario_can_belong_to_business_line_and_store_filters_by_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = ScenarioStore(Path(tmp) / "v211.db")
            store.save(
                Scenario(
                    id="content-xhs",
                    name="Content XHS",
                    description="Content optimization scenario.",
                    adapter_type="dummy_stock_signal",
                    business_line_id="content",
                )
            )
            store.save(
                Scenario(
                    id="quant-research",
                    name="Quant Research",
                    description="Quant optimization scenario.",
                    adapter_type="quant_research_demo",
                    business_line_id="quant",
                )
            )

            content = store.list(business_line_id="content")
            quant = store.list(business_line_id="quant")
            all_scenarios = store.list()

        self.assertEqual([item.id for item in content], ["content-xhs"])
        self.assertEqual([item.id for item in quant], ["quant-research"])
        self.assertEqual(len(all_scenarios), 2)

    def test_checkpoint_ai_exposes_distinct_runtime_and_proposal_policy_engines(self) -> None:
        checkpoint_ai = CheckpointAI()

        self.assertTrue(hasattr(checkpoint_ai.policy_engine, "evaluate_action"))
        self.assertIsInstance(checkpoint_ai.scenario_policy, ScenarioPolicy)


if __name__ == "__main__":
    unittest.main()
