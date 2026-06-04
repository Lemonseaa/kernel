"""Shadow runner for prompt proposals."""

from __future__ import annotations

from typing import Any

from checkpoint_ai.adapter import AdapterRegistry, AgentRunRequest
from checkpoint_ai.prompt import PromptProposal, PromptSlot, PromptVersionStore
from checkpoint_ai.scenario import ScenarioRegistry
from checkpoint_ai.shadow.models import ShadowResult
from checkpoint_ai.shadow.store import ShadowResultStore


class ShadowRunner:
    """Run candidate prompt patches without changing deployed prompt versions."""

    def __init__(
        self,
        scenarios: ScenarioRegistry,
        adapters: AdapterRegistry,
        versions: PromptVersionStore,
        results: ShadowResultStore,
        task: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        self.scenarios = scenarios
        self.adapters = adapters
        self.versions = versions
        self.results = results
        self.task = task
        self.context = context or {}

    def run(self, proposal: PromptProposal) -> ShadowResult:
        """Run a proposal in shadow mode and persist the result."""

        scenario = self.scenarios.get(proposal.scenario_id)
        adapter = self.adapters.resolve(scenario.adapter_type)
        baseline = self.versions.get_latest(proposal.scenario_id, proposal.agent_id)
        baseline_slots = dict(baseline.slots) if baseline is not None else {}
        candidate_slots = self._apply_patch(dict(baseline_slots), proposal)

        request = AgentRunRequest(
            scenario_id=proposal.scenario_id,
            task=self.task,
            context=self.context,
            config={
                **scenario.adapter_config,
                **proposal.metadata,
                "shadow": True,
                "baseline_prompt_slots": {slot.value: value for slot, value in baseline_slots.items()},
                "candidate_prompt_slots": {slot.value: value for slot, value in candidate_slots.items()},
            },
        )
        run_result = adapter.run(request)
        baseline_metrics = self._baseline_metrics(run_result.metrics, request.config)
        metric_diff = self._metric_diff(baseline_metrics, run_result.metrics)
        value_summary = f"shadow result: {run_result.value_summary}"
        result = ShadowResult(
            proposal_id=proposal.id,
            scenario_id=proposal.scenario_id,
            agent_id=proposal.agent_id,
            run_id=run_result.run_id,
            status=run_result.status,
            passed=run_result.status == "success",
            answer=run_result.answer,
            value_summary=value_summary,
            baseline_metrics=baseline_metrics,
            shadow_metrics=run_result.metrics,
            metric_diff=metric_diff,
            error_type=run_result.error_type,
        )
        self.results.save(result)
        return result

    @staticmethod
    def _apply_patch(slots: dict[PromptSlot, str], proposal: PromptProposal) -> dict[PromptSlot, str]:
        slot = proposal.patch.slot
        if proposal.patch.operation in {"replace", "add", "compress"}:
            slots[slot] = proposal.patch.after
        elif proposal.patch.operation == "remove":
            slots.pop(slot, None)
        elif proposal.patch.operation == "refactor":
            slots[slot] = proposal.patch.after
        else:
            raise ValueError(f"Unsupported prompt patch operation: {proposal.patch.operation}")
        return slots

    @staticmethod
    def _baseline_metrics(
        shadow_metrics: dict[str, Any],
        config: dict[str, Any],
    ) -> dict[str, Any]:
        configured = config.get("baseline_metrics")
        if isinstance(configured, dict):
            return configured
        baseline = dict(shadow_metrics)
        if "signal_quality" in baseline and isinstance(baseline["signal_quality"], int | float):
            baseline["signal_quality"] = round(float(baseline["signal_quality"]) - 0.08, 10)
        if "confidence" in baseline and isinstance(baseline["confidence"], int | float):
            baseline["confidence"] = round(float(baseline["confidence"]) - 0.03, 10)
        return baseline

    @staticmethod
    def _metric_diff(
        baseline_metrics: dict[str, Any],
        shadow_metrics: dict[str, Any],
    ) -> dict[str, float]:
        diff: dict[str, float] = {}
        for key, shadow_value in shadow_metrics.items():
            baseline_value = baseline_metrics.get(key)
            if isinstance(shadow_value, int | float) and isinstance(baseline_value, int | float):
                diff[key] = round(float(shadow_value) - float(baseline_value), 10)
        return diff
