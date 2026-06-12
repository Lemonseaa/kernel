"""V2.8 stable end-to-end acceptance tests."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from checkpoint_ai.adapter import AdapterRegistry, OPCAgentAdapter
from checkpoint_ai.logs import RawLogStore, SummaryLogStore
from checkpoint_ai.loop import AgentLoopEngine, AgentLoopStore, LoopStatus
from checkpoint_ai.policy import ScenarioPolicy, ScenarioPolicyService
from checkpoint_ai.prompt import (
    PromptPatch,
    PromptProposal,
    PromptProposalStore,
    PromptSlot,
    PromptVersionStore,
)
from checkpoint_ai.reporting import ReportGenerator
from checkpoint_ai.scenario import Scenario, ScenarioRegistry, ScenarioRunner, ScenarioStore
from checkpoint_ai.shadow import ShadowResultStore, ShadowRunner


class V28V2StableTest(unittest.TestCase):
    """Prove V2.1-V2.7 work together as one loop."""

    def test_v2_stable_flow_runs_from_scenario_to_auto_apply(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "v28.db"
            script = self._write_fake_opc_agent(Path(tmp))
            scenario_store = ScenarioStore(db_path)
            scenario_store.save(
                Scenario(
                    id="opc-demo",
                    name="OPC demo",
                    description="V2 stable first demo scenario.",
                    adapter_type="opc_agent_demo",
                    adapter_config={"command": [sys.executable, str(script)], "cwd": tmp},
                )
            )

            scenarios = ScenarioRegistry()
            for scenario in scenario_store.list():
                scenarios.create(scenario)
            adapters = AdapterRegistry()
            adapters.register(OPCAgentAdapter())
            raw_logs = RawLogStore(db_path)
            summary_logs = SummaryLogStore(db_path)
            runner = ScenarioRunner(
                scenarios=scenarios,
                adapters=adapters,
                raw_logs=raw_logs,
                summary_logs=summary_logs,
            )
            versions = PromptVersionStore(db_path)
            versions.save_version(
                scenario_id="opc-demo",
                agent_id="writer",
                slots={PromptSlot.OUTPUT_FORMAT: "输出自然语言。"},
                reason="baseline",
            )
            proposals = PromptProposalStore(db_path)
            shadow_results = ShadowResultStore(db_path)
            shadow_runner = ShadowRunner(
                scenarios=scenarios,
                adapters=adapters,
                versions=versions,
                results=shadow_results,
                task="content_pipeline",
                context={"topic": "AI内容增长"},
            )
            policy_service = ScenarioPolicyService(
                policy=ScenarioPolicy(),
                proposals=proposals,
                versions=versions,
                shadow_runner=shadow_runner,
            )
            engine = AgentLoopEngine(
                scenario_runner=runner,
                proposals=proposals,
                policy_service=policy_service,
                shadow_results=shadow_results,
                loop_store=AgentLoopStore(db_path),
                proposal_factory=self._proposal_factory,
            )

            loop_run = engine.trigger_manual(
                scenario_id="opc-demo",
                task="content_pipeline",
                reason="V2.8端到端验收：从真实demo adapter触发完整优化闭环。",
                context={"topic": "AI内容增长"},
            )
            latest_prompt = versions.get_latest("opc-demo", "writer")
            raw = raw_logs.query_by_scenario("opc-demo")
            summaries = summary_logs.query_by_scenario("opc-demo")
            shadows = shadow_results.query_by_proposal(loop_run.proposal_id or "")
            proposal = proposals.get(loop_run.proposal_id or "")
            report = ReportGenerator(db_path).proposal(loop_run.proposal_id or "")

        self.assertEqual(loop_run.status, LoopStatus.COMPLETED)
        self.assertEqual(loop_run.policy_action, "auto_applied")
        self.assertEqual(len(raw), 1)
        self.assertEqual(len(summaries), 1)
        self.assertEqual(len(shadows), 1)
        self.assertIn("content_quality", loop_run.baseline_comparison)
        self.assertGreater(loop_run.baseline_comparison["content_quality"], 0)
        self.assertIsNotNone(latest_prompt)
        self.assertEqual(latest_prompt.slots[PromptSlot.OUTPUT_FORMAT], "输出 JSON。")
        self.assertIsNotNone(proposal)
        self.assertEqual(proposal.status.value, "applied")
        self.assertIn("Proposal Report", report)
        self.assertIn("比baseline好了还是差了", report)

    @staticmethod
    def _proposal_factory(scenario_id: str, run_metrics: dict[str, float]) -> PromptProposal:
        return PromptProposal(
            scenario_id=scenario_id,
            agent_id="writer",
            patch=PromptPatch(
                slot=PromptSlot.OUTPUT_FORMAT,
                operation="replace",
                before="输出自然语言。",
                after="输出 JSON。",
            ),
            reason=f"content_quality={run_metrics.get('content_quality', 0):.2f}，结构化输出更利于稳定评估。",
            expected_metric="content_quality",
        )

    @staticmethod
    def _write_fake_opc_agent(root: Path) -> Path:
        script = root / "fake_opc_agent_v28.py"
        script.write_text(
            "import json, sys\n"
            "request = json.loads(sys.stdin.read())\n"
            "is_shadow = bool(request.get('config', {}).get('shadow'))\n"
            "quality = 0.93 if is_shadow else 0.84\n"
            "topic = request.get('context', {}).get('topic', 'unknown')\n"
            "print(json.dumps({\n"
            "  'answer': f'OPC demo generated content for {topic}; shadow={is_shadow}',\n"
            "  'metrics': {'content_quality': quality, 'distribution_ready': 1.0},\n"
            "  'value_summary': f'OPC demo完成{topic}内容生成，content_quality={quality}',\n"
            "  'status': 'success'\n"
            "}, ensure_ascii=False))\n",
            encoding="utf-8",
        )
        return script


if __name__ == "__main__":
    unittest.main()
