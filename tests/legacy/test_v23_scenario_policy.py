"""V2.3 ScenarioPolicy tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from loop_harness.policy import PolicyLevel, ScenarioPolicy, ScenarioPolicyService
from loop_harness.prompt import (
    PromptPatch,
    PromptProposal,
    PromptProposalStatus,
    PromptProposalStore,
    PromptSlot,
    PromptVersionStore,
)


class FakeShadowRunner:
    """Minimal shadow runner used to prove policy gates execution order."""

    def __init__(self, passed: bool = True) -> None:
        self.passed = passed
        self.calls: list[str] = []

    def run(self, proposal: PromptProposal) -> bool:
        self.calls.append(proposal.id)
        return self.passed


class V23ScenarioPolicyTest(unittest.TestCase):
    """Validate policy classification and shadow gate behavior."""

    def test_policy_classifies_auto_approval_and_blocked(self) -> None:
        policy = ScenarioPolicy()

        auto = policy.evaluate(self._proposal(slot=PromptSlot.OUTPUT_FORMAT, operation="replace"))
        approval = policy.evaluate(self._proposal(slot=PromptSlot.ROLE, operation="replace"))
        blocked = policy.evaluate(self._proposal(slot=PromptSlot.GOAL, operation="refactor"))

        self.assertEqual(auto.level, PolicyLevel.AUTO)
        self.assertEqual(approval.level, PolicyLevel.APPROVAL)
        self.assertEqual(blocked.level, PolicyLevel.BLOCKED)
        self.assertIn("output_format", auto.reason)
        self.assertIn("role", approval.reason)
        self.assertIn("refactor", blocked.reason)

    def test_blocked_proposal_does_not_run_shadow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            proposal_store, version_store = self._stores(tmp)
            proposal = self._proposal(slot=PromptSlot.GOAL, operation="refactor")
            proposal_store.create(proposal)
            shadow = FakeShadowRunner()
            service = ScenarioPolicyService(
                policy=ScenarioPolicy(),
                proposals=proposal_store,
                versions=version_store,
                shadow_runner=shadow,
            )

            result = service.process(proposal.id)
            loaded = proposal_store.get(proposal.id)

        self.assertEqual(result.level, PolicyLevel.BLOCKED)
        self.assertEqual(shadow.calls, [])
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.status, PromptProposalStatus.REJECTED)
        self.assertEqual(loaded.metadata["policy_level"], "blocked")
        self.assertEqual(loaded.metadata["shadow_run"], False)

    def test_auto_and_approval_must_run_shadow(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            proposal_store, version_store = self._stores(tmp)
            auto = self._proposal(slot=PromptSlot.OUTPUT_FORMAT, operation="replace")
            approval = self._proposal(slot=PromptSlot.ROLE, operation="replace")
            proposal_store.create(auto)
            proposal_store.create(approval)
            shadow = FakeShadowRunner()
            service = ScenarioPolicyService(
                policy=ScenarioPolicy(),
                proposals=proposal_store,
                versions=version_store,
                shadow_runner=shadow,
            )

            auto_result = service.process(auto.id)
            approval_result = service.process(approval.id)

        self.assertEqual(auto_result.level, PolicyLevel.AUTO)
        self.assertEqual(approval_result.level, PolicyLevel.APPROVAL)
        self.assertEqual(shadow.calls, [auto.id, approval.id])

    def test_auto_applies_after_shadow_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            proposal_store, version_store = self._stores(tmp)
            version_store.save_version(
                scenario_id="scenario-1",
                agent_id="writer",
                slots={PromptSlot.OUTPUT_FORMAT: "输出自然语言。"},
                reason="初始输出格式。",
            )
            proposal = self._proposal(
                slot=PromptSlot.OUTPUT_FORMAT,
                operation="replace",
                before="输出自然语言。",
                after="输出 JSON。",
            )
            proposal_store.create(proposal)
            service = ScenarioPolicyService(
                policy=ScenarioPolicy(),
                proposals=proposal_store,
                versions=version_store,
                shadow_runner=FakeShadowRunner(passed=True),
            )

            result = service.process(proposal.id)
            latest = version_store.get_latest("scenario-1", "writer")
            loaded = proposal_store.get(proposal.id)

        self.assertEqual(result.level, PolicyLevel.AUTO)
        self.assertTrue(result.shadow_passed)
        self.assertIsNotNone(latest)
        self.assertEqual(latest.slots[PromptSlot.OUTPUT_FORMAT], "输出 JSON。")
        self.assertEqual(latest.reason, f"Applied proposal {proposal.id}: 结构化输出更稳定。")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.status, PromptProposalStatus.APPLIED)

    def test_approval_waits_for_human_after_shadow_passes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            proposal_store, version_store = self._stores(tmp)
            version_store.save_version(
                scenario_id="scenario-1",
                agent_id="writer",
                slots={PromptSlot.ROLE: "你是写手。"},
                reason="初始角色。",
            )
            proposal = self._proposal(slot=PromptSlot.ROLE, operation="replace")
            proposal_store.create(proposal)
            service = ScenarioPolicyService(
                policy=ScenarioPolicy(),
                proposals=proposal_store,
                versions=version_store,
                shadow_runner=FakeShadowRunner(passed=True),
            )

            result = service.process(proposal.id)
            latest = version_store.get_latest("scenario-1", "writer")
            loaded = proposal_store.get(proposal.id)

        self.assertEqual(result.level, PolicyLevel.APPROVAL)
        self.assertTrue(result.shadow_passed)
        self.assertIsNotNone(latest)
        self.assertEqual(latest.slots[PromptSlot.ROLE], "你是写手。")
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.status, PromptProposalStatus.APPROVED)
        self.assertEqual(loaded.metadata["awaiting_human_confirmation"], True)

    @staticmethod
    def _stores(tmp: str) -> tuple[PromptProposalStore, PromptVersionStore]:
        db_path = Path(tmp) / "v23.db"
        return PromptProposalStore(db_path), PromptVersionStore(db_path)

    @staticmethod
    def _proposal(
        slot: PromptSlot,
        operation: str,
        before: str = "before",
        after: str = "after",
    ) -> PromptProposal:
        return PromptProposal(
            scenario_id="scenario-1",
            agent_id="writer",
            patch=PromptPatch(
                slot=slot,
                operation=operation,
                before=before,
                after=after,
            ),
            reason="结构化输出更稳定。",
            expected_metric="schema_valid_rate",
        )


if __name__ == "__main__":
    unittest.main()
