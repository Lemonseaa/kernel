"""AgentLoopEngine for one-shot, explainable optimization loops."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Literal

from loop_harness.adapter import AgentRunResult
from loop_harness.loop.models import LoopRun, LoopStatus, LoopStep
from loop_harness.loop.store import AgentLoopStore
from loop_harness.policy import PolicyProcessResult, ScenarioPolicyService
from loop_harness.prompt import PromptProposal, PromptProposalStore
from loop_harness.scenario import ScenarioRunner
from loop_harness.shadow import ShadowResult, ShadowResultStore

ProposalFactory = Callable[[str, dict[str, float]], PromptProposal]


class AgentLoopEngine:
    """Orchestrate Trigger -> Run -> Policy -> Shadow -> Compare once."""

    def __init__(
        self,
        scenario_runner: ScenarioRunner,
        proposals: PromptProposalStore,
        policy_service: ScenarioPolicyService,
        shadow_results: ShadowResultStore,
        loop_store: AgentLoopStore,
        proposal_factory: ProposalFactory,
    ) -> None:
        self.scenario_runner = scenario_runner
        self.proposals = proposals
        self.policy_service = policy_service
        self.shadow_results = shadow_results
        self.loop_store = loop_store
        self.proposal_factory = proposal_factory

    def trigger_manual(
        self,
        scenario_id: str,
        task: str,
        reason: str,
        context: dict[str, Any] | None = None,
        config: dict[str, Any] | None = None,
    ) -> LoopRun:
        """Run one full loop from a manual trigger."""

        loop_run = LoopRun(
            scenario_id=scenario_id,
            trigger_type="manual",
            reason=reason,
            trigger={"reason": reason},
            task=task,
        )
        return self._execute(loop_run, context=context, config=config)

    def trigger_threshold(
        self,
        scenario_id: str,
        task: str,
        reason: str,
        metric: str,
        observed_value: float,
        threshold_value: float,
        direction: Literal["below", "above"] = "below",
        context: dict[str, Any] | None = None,
        config: dict[str, Any] | None = None,
    ) -> LoopRun:
        """Run one full loop when a threshold condition is met."""

        trigger_payload = {
            "reason": reason,
            "metric": metric,
            "observed_value": observed_value,
            "threshold_value": threshold_value,
            "direction": direction,
        }
        loop_run = LoopRun(
            scenario_id=scenario_id,
            trigger_type="threshold",
            reason=reason,
            trigger=trigger_payload,
            task=task,
        )
        if not self._threshold_met(observed_value, threshold_value, direction):
            loop_run.add_step(
                LoopStep.TRIGGER,
                "阈值条件未满足，闭环跳过。",
                trigger_payload,
            )
            loop_run.status = LoopStatus.SKIPPED
            loop_run.changed_summary = "未触发执行，没有改变线上状态。"
            loop_run.add_step(LoopStep.END, "闭环结束：threshold skipped。")
            self.loop_store.save(loop_run)
            return loop_run
        return self._execute(loop_run, context=context, config=config)

    def get_loop(self, loop_id: str) -> LoopRun | None:
        """Return one loop run."""

        return self.loop_store.get(loop_id)

    def get_status(self, loop_id: str) -> dict[str, Any]:
        """Return concise human-facing loop status."""

        loop_run = self.loop_store.get(loop_id)
        if loop_run is None:
            raise KeyError(f"Loop run not found: {loop_id}")
        return {
            "id": loop_run.id,
            "scenario_id": loop_run.scenario_id,
            "status": loop_run.status.value,
            "trigger_type": loop_run.trigger_type,
            "step_count": len(loop_run.steps),
            "latest_step": loop_run.steps[-1].step.value if loop_run.steps else None,
            "changed_summary": loop_run.changed_summary,
        }

    def answer_core_questions(self, loop_id: str) -> dict[str, str]:
        """Answer the four V2.5 audit questions for one loop."""

        loop_run = self.loop_store.get(loop_id)
        if loop_run is None:
            raise KeyError(f"Loop run not found: {loop_id}")
        comparison = (
            "无shadow对比结果。"
            if not loop_run.baseline_comparison
            else f"metrics_diff={loop_run.baseline_comparison}"
        )
        return {
            "为什么运行？": loop_run.reason,
            "发生了什么？": (
                f"adapter_run={loop_run.adapter_run_id}, status={loop_run.adapter_status}, "
                f"summary={loop_run.adapter_value_summary}"
            ),
            "改变了什么？": loop_run.changed_summary,
            "比baseline好了还是差了？": comparison,
        }

    def _execute(
        self,
        loop_run: LoopRun,
        context: dict[str, Any] | None,
        config: dict[str, Any] | None,
    ) -> LoopRun:
        loop_run.add_step(LoopStep.TRIGGER, "闭环被触发。", loop_run.trigger)
        self.loop_store.save(loop_run)
        try:
            run_result = self._run_adapter(loop_run, context=context, config=config)
            proposal = self._create_proposal(loop_run, run_result)
            policy_result = self._process_policy(loop_run, proposal.id)
            self._record_shadow_and_compare(loop_run, proposal.id)
            self._record_apply_or_notify(loop_run, policy_result)
            loop_run.status = LoopStatus.COMPLETED
            loop_run.add_step(LoopStep.END, "闭环结束：completed。")
        except Exception as exc:
            loop_run.status = LoopStatus.FAILED
            loop_run.changed_summary = f"闭环失败，没有确认可用改变：{exc}"
            loop_run.add_step(LoopStep.END, f"闭环结束：failed，原因：{exc}")
        self.loop_store.save(loop_run)
        return loop_run

    def _run_adapter(
        self,
        loop_run: LoopRun,
        context: dict[str, Any] | None,
        config: dict[str, Any] | None,
    ) -> AgentRunResult:
        loop_run.add_step(LoopStep.RUN, "执行scenario adapter。")
        run_result = self.scenario_runner.run_scenario(
            scenario_id=loop_run.scenario_id,
            task=loop_run.task,
            context=context,
            config=config,
        )
        loop_run.adapter_run_id = run_result.run_id
        loop_run.adapter_status = run_result.status
        loop_run.adapter_value_summary = run_result.value_summary
        loop_run.add_step(
            LoopStep.RECORD,
            "ScenarioRunner已写入raw log和summary log。",
            {"run_id": run_result.run_id, "status": run_result.status},
        )
        loop_run.add_step(
            LoopStep.EVALUATE,
            "读取adapter返回的metrics作为本次评估输入。",
            {"metrics": run_result.metrics, "value_summary": run_result.value_summary},
        )
        self.loop_store.save(loop_run)
        return run_result

    def _create_proposal(self, loop_run: LoopRun, run_result: AgentRunResult) -> PromptProposal:
        metrics = self._numeric_metrics(run_result.metrics)
        proposal = self.proposal_factory(loop_run.scenario_id, metrics)
        proposal_id = self.proposals.create(proposal)
        loop_run.proposal_id = proposal_id
        loop_run.add_step(
            LoopStep.PROPOSAL,
            "创建prompt patch proposal。",
            {
                "proposal_id": proposal_id,
                "slot": proposal.patch.slot.value,
                "expected_metric": proposal.expected_metric,
            },
        )
        self.loop_store.save(loop_run)
        return proposal

    def _process_policy(self, loop_run: LoopRun, proposal_id: str) -> PolicyProcessResult:
        result = self.policy_service.process(proposal_id)
        loop_run.policy_level = result.level.value
        loop_run.policy_action = result.action
        loop_run.add_step(
            LoopStep.POLICY,
            "Policy已完成，BLOCKED不会运行shadow。",
            {
                "policy_level": result.level.value,
                "policy_reason": result.policy_reason,
                "action": result.action,
            },
        )
        shadow_message = "Shadow已运行。" if result.shadow_ran else "Policy阻止shadow运行。"
        loop_run.add_step(
            LoopStep.SHADOW,
            shadow_message,
            {"shadow_ran": result.shadow_ran, "shadow_passed": result.shadow_passed},
        )
        self.loop_store.save(loop_run)
        return result

    def _record_shadow_and_compare(self, loop_run: LoopRun, proposal_id: str) -> None:
        shadow_result = self._latest_shadow_result(proposal_id)
        if shadow_result is None:
            loop_run.add_step(LoopStep.COMPARE, "没有shadow结果，无法和baseline对比。")
            return
        loop_run.shadow_result_id = shadow_result.id
        loop_run.baseline_comparison = shadow_result.business_metric_diff or shadow_result.metric_diff
        loop_run.add_step(
            LoopStep.COMPARE,
            "Shadow result已和baseline metrics对比。",
            {
                "shadow_result_id": shadow_result.id,
                "business_metric_diff": loop_run.baseline_comparison,
                "comparison_result": shadow_result.comparison_result,
            },
        )
        self.loop_store.save(loop_run)

    def _record_apply_or_notify(
        self,
        loop_run: LoopRun,
        policy_result: PolicyProcessResult,
    ) -> None:
        if policy_result.action == "auto_applied":
            loop_run.changed_summary = (
                f"action=auto_applied; Proposal {policy_result.proposal_id} 已自动应用。"
            )
        elif policy_result.action == "awaiting_human_confirmation":
            loop_run.changed_summary = (
                f"action=awaiting_human_confirmation; "
                f"Proposal {policy_result.proposal_id} 等待人工确认。"
            )
        elif policy_result.action == "blocked":
            loop_run.changed_summary = (
                f"action=blocked; Proposal {policy_result.proposal_id} 被Policy拒绝。"
            )
        else:
            loop_run.changed_summary = (
                f"action={policy_result.action}; "
                f"Proposal {policy_result.proposal_id} 未应用：{policy_result.action}。"
            )
        loop_run.add_step(
            LoopStep.APPLY_NOTIFY,
            "根据policy结果应用或通知。",
            {"action": policy_result.action, "changed_summary": loop_run.changed_summary},
        )
        self.loop_store.save(loop_run)

    def _latest_shadow_result(self, proposal_id: str) -> ShadowResult | None:
        results = self.shadow_results.query_by_proposal(proposal_id)
        return results[-1] if results else None

    @staticmethod
    def _numeric_metrics(metrics: dict[str, Any]) -> dict[str, float]:
        numeric: dict[str, float] = {}
        for key, value in metrics.items():
            if isinstance(value, int | float):
                numeric[key] = float(value)
        return numeric

    @staticmethod
    def _threshold_met(
        observed_value: float,
        threshold_value: float,
        direction: Literal["below", "above"],
    ) -> bool:
        if direction == "below":
            return observed_value < threshold_value
        return observed_value > threshold_value
