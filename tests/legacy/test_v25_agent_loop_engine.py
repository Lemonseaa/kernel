"""V2.5 AgentLoopEngine tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from checkpoint_ai.adapter import AdapterRegistry, DummyAdapter
from checkpoint_ai.logs import RawLogStore, SummaryLogStore
from checkpoint_ai.loop import AgentLoopEngine, AgentLoopStore, LoopStatus, LoopStep
from checkpoint_ai.policy import ScenarioPolicy, ScenarioPolicyService
from checkpoint_ai.prompt import (
    PromptPatch,
    PromptProposal,
    PromptProposalStore,
    PromptSlot,
    PromptVersionStore,
)
from checkpoint_ai.scenario import Scenario, ScenarioRegistry, ScenarioRunner
from checkpoint_ai.shadow import ShadowResultStore, ShadowRunner


class V25AgentLoopEngineTest(unittest.TestCase):
    """Validate one-shot loop orchestration across V2.1-V2.4 modules."""

    def test_manual_trigger_executes_full_loop_and_answers_core_questions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            engine, stores = self._build_engine(tmp)

            loop_run = engine.trigger_manual(
                scenario_id="scenario-1",
                task="analyze_signal",
                reason="人工要求检查输出格式是否能提升信号质量。",
                context={"symbol": "AAPL"},
            )
            answers = engine.answer_core_questions(loop_run.id)
            latest_prompt = stores["versions"].get_latest("scenario-1", "writer")
            shadow_results = stores["shadow_results"].query_by_proposal(loop_run.proposal_id or "")

        self.assertEqual(loop_run.status, LoopStatus.COMPLETED)
        self.assertEqual(loop_run.trigger_type, "manual")
        self.assertEqual(loop_run.policy_action, "auto_applied")
        self.assertIsNotNone(latest_prompt)
        self.assertEqual(latest_prompt.slots[PromptSlot.OUTPUT_FORMAT], "输出 JSON。")
        self.assertEqual(len(shadow_results), 1)
        self.assertIn("人工要求检查", answers["为什么运行？"])
        self.assertIn("success", answers["发生了什么？"])
        self.assertIn("auto_applied", answers["改变了什么？"])
        self.assertIn("signal_quality", answers["比baseline好了还是差了？"])

    def test_every_required_step_has_log_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            engine, _ = self._build_engine(tmp)

            loop_run = engine.trigger_manual(
                scenario_id="scenario-1",
                task="analyze_signal",
                reason="验证每一步都有记录。",
            )

        steps = [step.step for step in loop_run.steps]
        self.assertEqual(
            steps,
            [
                LoopStep.TRIGGER,
                LoopStep.RUN,
                LoopStep.RECORD,
                LoopStep.EVALUATE,
                LoopStep.PROPOSAL,
                LoopStep.POLICY,
                LoopStep.SHADOW,
                LoopStep.COMPARE,
                LoopStep.APPLY_NOTIFY,
                LoopStep.END,
            ],
        )
        for step in loop_run.steps:
            self.assertTrue(step.message)

    def test_threshold_trigger_runs_when_threshold_is_met(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            engine, _ = self._build_engine(tmp)

            loop_run = engine.trigger_threshold(
                scenario_id="scenario-1",
                task="analyze_signal",
                reason="signal_quality低于预期，需要触发优化闭环。",
                metric="signal_quality",
                observed_value=0.62,
                threshold_value=0.7,
                direction="below",
            )

        self.assertEqual(loop_run.status, LoopStatus.COMPLETED)
        self.assertEqual(loop_run.trigger_type, "threshold")
        self.assertEqual(loop_run.trigger["metric"], "signal_quality")

    def test_threshold_trigger_can_skip_without_running_adapter(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            engine, stores = self._build_engine(tmp)

            loop_run = engine.trigger_threshold(
                scenario_id="scenario-1",
                task="analyze_signal",
                reason="指标还没有跌破阈值，不应该消耗shadow资源。",
                metric="signal_quality",
                observed_value=0.82,
                threshold_value=0.7,
                direction="below",
            )
            raw_logs = stores["raw_logs"].query_by_scenario("scenario-1")
            shadow_results = stores["shadow_results"].query_by_scenario("scenario-1")

        self.assertEqual(loop_run.status, LoopStatus.SKIPPED)
        self.assertEqual(raw_logs, [])
        self.assertEqual(shadow_results, [])
        self.assertEqual([step.step for step in loop_run.steps], [LoopStep.TRIGGER, LoopStep.END])

    def test_loop_status_can_be_viewed_after_trigger(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            engine, _ = self._build_engine(tmp)
            loop_run = engine.trigger_manual(
                scenario_id="scenario-1",
                task="analyze_signal",
                reason="用户需要随时查看闭环状态。",
            )

            status = engine.get_status(loop_run.id)
            loaded = engine.get_loop(loop_run.id)

        self.assertEqual(status["status"], "completed")
        self.assertEqual(status["scenario_id"], "scenario-1")
        self.assertEqual(status["step_count"], 10)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.id, loop_run.id)

    @staticmethod
    def _build_engine(tmp: str) -> tuple[AgentLoopEngine, dict[str, object]]:
        db_path = Path(tmp) / "v25.db"
        scenarios = ScenarioRegistry()
        scenarios.create(
            Scenario(
                id="scenario-1",
                name="Quant demo",
                description="One-shot loop scenario.",
                adapter_type="dummy_stock_signal",
            )
        )
        adapters = AdapterRegistry()
        adapters.register(DummyAdapter())
        raw_logs = RawLogStore(db_path)
        summary_logs = SummaryLogStore(db_path)
        scenario_runner = ScenarioRunner(
            scenarios=scenarios,
            adapters=adapters,
            raw_logs=raw_logs,
            summary_logs=summary_logs,
        )
        versions = PromptVersionStore(db_path)
        versions.save_version(
            scenario_id="scenario-1",
            agent_id="writer",
            slots={PromptSlot.OUTPUT_FORMAT: "输出自然语言。"},
            reason="baseline prompt",
        )
        proposals = PromptProposalStore(db_path)
        shadow_results = ShadowResultStore(db_path)
        shadow_runner = ShadowRunner(
            scenarios=scenarios,
            adapters=adapters,
            versions=versions,
            results=shadow_results,
            task="analyze_signal",
            context={"symbol": "AAPL"},
        )
        policy_service = ScenarioPolicyService(
            policy=ScenarioPolicy(),
            proposals=proposals,
            versions=versions,
            shadow_runner=shadow_runner,
        )

        def proposal_factory(scenario_id: str, run_metrics: dict[str, float]) -> PromptProposal:
            return PromptProposal(
                scenario_id=scenario_id,
                agent_id="writer",
                patch=PromptPatch(
                    slot=PromptSlot.OUTPUT_FORMAT,
                    operation="replace",
                    before="输出自然语言。",
                    after="输出 JSON。",
                ),
                reason=f"当前signal_quality={run_metrics.get('signal_quality', 0):.2f}，结构化输出便于评估。",
                expected_metric="signal_quality",
            )

        return (
            AgentLoopEngine(
                scenario_runner=scenario_runner,
                proposals=proposals,
                policy_service=policy_service,
                shadow_results=shadow_results,
                loop_store=AgentLoopStore(db_path),
                proposal_factory=proposal_factory,
            ),
            {
                "raw_logs": raw_logs,
                "summary_logs": summary_logs,
                "versions": versions,
                "proposals": proposals,
                "shadow_results": shadow_results,
            },
        )


if __name__ == "__main__":
    unittest.main()
