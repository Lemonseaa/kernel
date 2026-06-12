"""V4.2 adapter capability hardening tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from checkpoint_ai.adapter import (
    AdapterCapabilities,
    AdapterRegistry,
    AgentAdapter,
    AgentRunRequest,
    AgentRunResult,
    CapabilitySupport,
    DummyAdapter,
)
from checkpoint_ai.prompt import PromptPatch, PromptProposal, PromptSlot, PromptVersionStore
from checkpoint_ai.scenario import Scenario, ScenarioRegistry
from checkpoint_ai.shadow import ShadowResultStore, ShadowRunner


class V42AdapterRegistryTest(unittest.TestCase):
    """Validate structured adapter capabilities and explicit degradation."""

    def test_adapter_capabilities_are_structured(self) -> None:
        caps = DummyAdapter().capabilities()

        self.assertIsInstance(caps, AdapterCapabilities)
        self.assertEqual(caps.metrics_capture, CapabilitySupport.SUPPORTED)
        self.assertEqual(caps.structured_input, CapabilitySupport.SUPPORTED)

    def test_registry_lists_and_queries_capabilities(self) -> None:
        registry = AdapterRegistry()
        registry.register(DummyAdapter())

        self.assertTrue(registry.supports("dummy_stock_signal", "metrics_capture"))
        self.assertFalse(registry.supports("dummy_stock_signal", "continuous_params"))
        description = registry.describe()[0]
        self.assertEqual(description.name, "dummy_stock_signal")
        self.assertEqual(description.capabilities.metrics_capture, CapabilitySupport.SUPPORTED)

    def test_shadow_runner_fails_explicitly_when_shadow_run_unsupported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "v42.db"
            scenarios = ScenarioRegistry()
            scenarios.create(
                Scenario(
                    id="scenario-1",
                    name="No Shadow",
                    description="unsupported shadow",
                    adapter_type="no_shadow",
                )
            )
            adapters = AdapterRegistry()
            adapters.register(_NoShadowAdapter())
            versions = PromptVersionStore(db_path)
            versions.save_version(
                scenario_id="scenario-1",
                agent_id="writer",
                slots={PromptSlot.CONSTRAINTS: "baseline"},
                reason="baseline",
            )
            runner = ShadowRunner(
                scenarios=scenarios,
                adapters=adapters,
                versions=versions,
                results=ShadowResultStore(db_path),
                task="write",
            )

            result = runner.run(
                PromptProposal(
                    scenario_id="scenario-1",
                    agent_id="writer",
                    patch=PromptPatch(
                        slot=PromptSlot.CONSTRAINTS,
                        operation="replace",
                        before="baseline",
                        after="candidate",
                    ),
                    reason="test unsupported shadow",
                    expected_metric="score",
                )
            )

            self.assertEqual(result.status, "failed")
            self.assertFalse(result.passed)
            self.assertEqual(result.error_type, "unsupported_capability")
            self.assertIn("shadow_run unsupported", result.value_summary)


class _NoShadowAdapter(AgentAdapter):
    @property
    def name(self) -> str:
        return "no_shadow"

    @property
    def supported_task_types(self) -> list[str]:
        return ["write"]

    def run(self, request: AgentRunRequest) -> AgentRunResult:
        return AgentRunResult(
            scenario_id=request.scenario_id,
            task=request.task,
            answer="should not run",
            metrics={},
            value_summary="should not run",
            status="success",
        )

    def capabilities(self) -> AdapterCapabilities:
        return AdapterCapabilities(
            metrics_capture=CapabilitySupport.SUPPORTED,
            shadow_run=CapabilitySupport.UNSUPPORTED,
        )


if __name__ == "__main__":
    unittest.main()
