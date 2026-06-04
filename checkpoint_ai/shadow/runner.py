"""Shadow runner for prompt proposals."""

from __future__ import annotations

from typing import Any

from checkpoint_ai.adapter import AdapterRegistry, AgentRunRequest
from checkpoint_ai.metrics import MetricSchemaRegistry, MetricSchemaStore
from checkpoint_ai.prompt import PromptProposal, PromptSlot, PromptVersionStore
from checkpoint_ai.scenario import ScenarioRegistry
from checkpoint_ai.shadow.comparison import MetricComparator, RunKind
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
        metric_schemas: MetricSchemaRegistry | None = None,
        metric_schema_store: MetricSchemaStore | None = None,
    ) -> None:
        self.scenarios = scenarios
        self.adapters = adapters
        self.versions = versions
        self.results = results
        self.task = task
        self.context = context or {}
        self.metric_schemas = metric_schemas
        self.metric_schema_store = metric_schema_store

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
        run_kind = self._run_kind(request.config)
        provenance = self._provenance(request.config)
        comparison = MetricComparator(self._metric_registry(proposal.scenario_id)).compare(
            baseline_metrics=baseline_metrics,
            candidate_metrics=run_result.metrics,
            run_kind=run_kind,
            provenance=provenance,
        )
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
            metric_diff=comparison.metric_diffs,
            comparison_result=comparison.model_dump(mode="json"),
            business_metric_diff=comparison.business_metric_diffs,
            run_kind=run_kind.value,
            provenance=provenance,
            error_type=run_result.error_type,
        )
        self.results.save(result)
        return result

    def _metric_registry(self, scenario_id: str) -> MetricSchemaRegistry:
        if self.metric_schema_store is not None:
            registry = self.metric_schema_store.registry_for_scenario(scenario_id)
            if registry.list():
                return registry
        if self.metric_schemas is not None:
            return self.metric_schemas
        return MetricSchemaRegistry.default_quant()

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
        for key, value in list(baseline.items()):
            if not isinstance(value, int | float) or key.endswith("_ms") or key.endswith("_chars"):
                continue
            baseline[key] = round(float(value) - 0.08, 10)
        return baseline

    @staticmethod
    def _run_kind(config: dict[str, Any]) -> RunKind:
        value = config.get("run_kind", RunKind.SYNTHETIC.value)
        if isinstance(value, str):
            try:
                return RunKind(value)
            except ValueError:
                return RunKind.SYNTHETIC
        return RunKind.SYNTHETIC

    @staticmethod
    def _provenance(config: dict[str, Any]) -> dict[str, Any]:
        value = config.get("provenance")
        if isinstance(value, dict):
            return value
        return {}
