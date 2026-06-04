"""Scenario runner that connects scenarios, adapters, and logs."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import Any

from checkpoint_ai.adapter import AdapterRegistry, AgentAdapter, AgentRunRequest, AgentRunResult
from checkpoint_ai.logs import RawLogStore, SummaryLogStore
from checkpoint_ai.scenario.registry import ScenarioRegistry


class ScenarioRunner:
    """Run a scenario through its configured adapter and persist logs."""

    def __init__(
        self,
        scenarios: ScenarioRegistry,
        adapters: AdapterRegistry,
        raw_logs: RawLogStore,
        summary_logs: SummaryLogStore,
        timeout_seconds: float = 30.0,
    ) -> None:
        self.scenarios = scenarios
        self.adapters = adapters
        self.raw_logs = raw_logs
        self.summary_logs = summary_logs
        self.timeout_seconds = timeout_seconds

    def run_scenario(
        self,
        scenario_id: str,
        task: str,
        context: dict[str, Any] | None = None,
        config: dict[str, Any] | None = None,
    ) -> AgentRunResult:
        """Run a scenario and record raw and summary logs."""

        scenario = self.scenarios.get(scenario_id)
        adapter = self.adapters.resolve(scenario.adapter_type)
        request = AgentRunRequest(
            scenario_id=scenario.id,
            task=task,
            context=context or {},
            config={**scenario.adapter_config, **(config or {})},
        )

        try:
            result = self._run_adapter_with_timeout(adapter, request)
        except TimeoutError:
            result = AgentRunResult(
                scenario_id=scenario.id,
                task=task,
                answer="Adapter timed out.",
                metrics={},
                value_summary="本次运行超时，不能作为有效baseline样本。",
                status="failed",
                error_type="timeout",
            )
        except Exception as exc:
            result = AgentRunResult(
                scenario_id=scenario.id,
                task=task,
                answer=f"Adapter error: {exc}",
                metrics={},
                value_summary=f"本次运行发生adapter_error：{exc}，不能作为有效baseline样本。",
                status="failed",
                error_type="adapter_error",
            )

        self.raw_logs.save(result.run_id, request, result)
        self.summary_logs.save(result)
        return result

    def _run_adapter_with_timeout(self, adapter: AgentAdapter, request: AgentRunRequest) -> AgentRunResult:
        """Run a sync adapter with a timeout boundary."""

        executor = ThreadPoolExecutor(max_workers=1)
        try:
            future = executor.submit(adapter.run, request)
            return future.result(timeout=self.timeout_seconds)
        finally:
            executor.shutdown(wait=False, cancel_futures=True)
