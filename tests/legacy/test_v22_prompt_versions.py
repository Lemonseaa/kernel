"""V2.2 PromptVersionStore + PromptProposal tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from pydantic import ValidationError

from loop_harness.prompt import (
    PromptPatch,
    PromptProposal,
    PromptProposalStatus,
    PromptProposalStore,
    PromptSlot,
    PromptVersionStore,
)
from loop_harness.scenario import Scenario, ScenarioRegistry


class V22PromptVersionTest(unittest.TestCase):
    """Validate prompt versioning and manual proposal contracts."""

    def test_save_prompt_version_with_reason_and_list_history(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            scenario = self._create_scenario()
            store = PromptVersionStore(Path(tmp) / "v22.db")

            first = store.save_version(
                scenario_id=scenario.id,
                agent_id="risk_manager",
                slots={
                    PromptSlot.ROLE: "你是风险经理。",
                    PromptSlot.GOAL: "识别不可接受的交易风险。",
                },
                reason="建立风险经理初始prompt。",
            )
            second = store.save_version(
                scenario_id=scenario.id,
                agent_id="risk_manager",
                slots={
                    PromptSlot.ROLE: "你是风险经理。",
                    PromptSlot.GOAL: "识别不可接受的交易风险，并给出硬性拒绝原因。",
                },
                reason="增加硬性拒绝说明。",
            )

            history = store.history(scenario.id, "risk_manager")
            latest = store.get_latest(scenario.id, "risk_manager")

        self.assertEqual([version.id for version in history], [first.id, second.id])
        self.assertIsNotNone(latest)
        self.assertEqual(latest.id, second.id)
        self.assertEqual(latest.reason, "增加硬性拒绝说明。")
        self.assertEqual(latest.slots[PromptSlot.GOAL], "识别不可接受的交易风险，并给出硬性拒绝原因。")

    def test_rollback_to_previous_prompt_version(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            scenario = self._create_scenario()
            store = PromptVersionStore(Path(tmp) / "v22.db")
            first = store.save_version(
                scenario_id=scenario.id,
                agent_id="title_agent",
                slots={PromptSlot.GOAL: "生成标题。"},
                reason="初始版本。",
            )
            store.save_version(
                scenario_id=scenario.id,
                agent_id="title_agent",
                slots={PromptSlot.GOAL: "生成包含数字的标题。"},
                reason="测试数字标题。",
            )

            rolled_back = store.rollback(scenario.id, "title_agent", reason="数字标题效果不稳定。")
            latest = store.get_latest(scenario.id, "title_agent")

        self.assertEqual(rolled_back.parent_version_id, first.id)
        self.assertEqual(rolled_back.slots[PromptSlot.GOAL], "生成标题。")
        self.assertEqual(rolled_back.reason, "Rollback: 数字标题效果不稳定。")
        self.assertIsNotNone(latest)
        self.assertEqual(latest.id, rolled_back.id)

    def test_create_prompt_proposal_requires_reason_and_expected_metric(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            scenario = self._create_scenario()
            store = PromptProposalStore(Path(tmp) / "v22.db")
            proposal = PromptProposal(
                scenario_id=scenario.id,
                agent_id="risk_manager",
                patch=PromptPatch(
                    slot=PromptSlot.CONSTRAINTS,
                    operation="replace",
                    before="回撤较大时提醒用户。",
                    after="样本外最大回撤超过本金约束时必须拒绝。",
                ),
                reason="Risk Manager 最近没有拦住高回撤策略。",
                expected_metric="max_drawdown_rejection_rate",
            )

            proposal_id = store.create(proposal)
            loaded = store.get(proposal_id)

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.reason, "Risk Manager 最近没有拦住高回撤策略。")
        self.assertEqual(loaded.expected_metric, "max_drawdown_rejection_rate")
        self.assertEqual(loaded.patch.slot, PromptSlot.CONSTRAINTS)

        with self.assertRaises(ValidationError):
            PromptProposal(
                scenario_id=scenario.id,
                agent_id="risk_manager",
                patch=PromptPatch(
                    slot=PromptSlot.CONSTRAINTS,
                    operation="replace",
                    before="old",
                    after="new",
                ),
                reason="",
                expected_metric="max_drawdown",
            )

        with self.assertRaises(ValidationError):
            PromptProposal(
                scenario_id=scenario.id,
                agent_id="risk_manager",
                patch=PromptPatch(
                    slot=PromptSlot.CONSTRAINTS,
                    operation="replace",
                    before="old",
                    after="new",
                ),
                reason="需要改善风险拒绝。",
                expected_metric="",
            )

    def test_list_proposals_by_status_and_update_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            scenario = self._create_scenario()
            store = PromptProposalStore(Path(tmp) / "v22.db")
            first_id = store.create(
                PromptProposal(
                    scenario_id=scenario.id,
                    agent_id="risk_manager",
                    patch=PromptPatch(
                        slot=PromptSlot.OUTPUT_FORMAT,
                        operation="replace",
                        before="输出自然语言。",
                        after="输出 JSON，包含 decision/reason/risk_score。",
                    ),
                    reason="结构化输出方便后续评估。",
                    expected_metric="schema_valid_rate",
                )
            )
            second_id = store.create(
                PromptProposal(
                    scenario_id=scenario.id,
                    agent_id="risk_manager",
                    patch=PromptPatch(
                        slot=PromptSlot.TOOLS_POLICY,
                        operation="replace",
                        before="可自由调用新闻工具。",
                        after="仅事件驱动策略调用新闻工具。",
                    ),
                    reason="降低无关新闻噪声。",
                    expected_metric="tool_noise_rate",
                )
            )

            store.update_status(first_id, PromptProposalStatus.APPROVED)
            pending = store.list(status=PromptProposalStatus.PROPOSED)
            approved = store.list(status=PromptProposalStatus.APPROVED)

        self.assertEqual([proposal.id for proposal in pending], [second_id])
        self.assertEqual([proposal.id for proposal in approved], [first_id])

    @staticmethod
    def _create_scenario() -> Scenario:
        registry = ScenarioRegistry()
        return registry.create(
            Scenario(
                name="Quant demo",
                description="Prompt version scenario.",
                adapter_type="dummy_stock_signal",
            )
        )


if __name__ == "__main__":
    unittest.main()
