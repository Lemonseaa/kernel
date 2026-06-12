"""V6.1 systemic risk fix tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from loop_harness.adapter import AdapterCapabilities, CapabilitySupport
from loop_harness.api import create_app
from loop_harness.auth import APIKeyManager
from loop_harness.autonomy import (
    AutoExecutionEligibility,
    AutonomyActionStatus,
    AutonomyActionStore,
)
from loop_harness.console import BackupManager
from loop_harness.decision import DecisionKind, DecisionLogStore
from loop_harness.demo import seed_console_demo
from loop_harness.prompt import PromptProposalStatus, PromptProposalStore
from loop_harness.shadow import ShadowResult, ShadowResultStore


class V61SystemicRiskFixTest(unittest.TestCase):
    """Validate V6.1 risk fixes that block unsafe autonomy."""

    def test_api_errors_use_envelope_and_decision_log_records_operator_actions(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "console.db"
            seeded = seed_console_demo(db_path, root / "backups")
            client, token = self._client(db_path, root / "backups")
            headers = self._auth(token)

            missing_comment = client.post(
                f"/api/approvals/{seeded['proposal_id']}/approve",
                json={"comment": ""},
                headers=headers,
            )
            approve = client.post(
                f"/api/approvals/{seeded['proposal_id']}/approve",
                json={"comment": "Shadow evidence is acceptable for demo approval."},
                headers=headers,
            )
            records = DecisionLogStore(db_path).list(source_id=str(seeded["proposal_id"]))

        self.assertEqual(missing_comment.status_code, 400)
        self.assertEqual(
            missing_comment.json(),
            {
                "code": "validation.operator_comment_required",
                "message": "Operator comment is required.",
                "details": {"source_id": str(seeded["proposal_id"])},
            },
        )
        self.assertEqual(approve.status_code, 200)
        self.assertEqual([record.kind for record in records], [DecisionKind.ERROR, DecisionKind.APPROVE])
        self.assertEqual(records[-1].comment, "Shadow evidence is acceptable for demo approval.")
        self.assertEqual(records[-1].scenario_id, "demo-quant")

    def test_restore_failure_and_success_are_audited_with_safety_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "console.db"
            backup_dir = root / "backups"
            seed_console_demo(db_path, backup_dir)
            backup = BackupManager(db_path, backup_dir).create_backup(label="before-v61")
            client, token = self._client(db_path, backup_dir)
            headers = self._auth(token)

            failed = client.post(
                f"/api/backups/{backup.id}/restore",
                json={"confirm": "NO"},
                headers=headers,
            )
            restored = client.post(
                f"/api/backups/{backup.id}/restore",
                json={"confirm": "RESTORE"},
                headers=headers,
            )
            records = DecisionLogStore(db_path).list(source_id=backup.id)

        self.assertEqual(failed.status_code, 400)
        self.assertEqual(failed.json()["code"], "backup.restore_confirmation_required")
        self.assertEqual(restored.status_code, 200)
        self.assertIsNotNone(restored.json()["pre_restore_backup_id"])
        self.assertEqual([record.kind for record in records], [DecisionKind.ERROR, DecisionKind.SYSTEM])
        self.assertEqual(records[-1].details["pre_restore_backup_id"], restored.json()["pre_restore_backup_id"])

    def test_failed_shadow_request_uses_error_envelope_and_decision_log(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "console.db"
            seed_console_demo(db_path, Path(tmp) / "backups")
            client, token = self._client(db_path, Path(tmp) / "backups")

            failed = client.post(
                "/api/shadows",
                json={"proposal_id": "missing-proposal"},
                headers=self._auth(token),
            )
            records = DecisionLogStore(db_path).list(source_id="missing-proposal")

        self.assertEqual(failed.status_code, 404)
        self.assertEqual(failed.json()["code"], "shadow.proposal_not_found")
        self.assertEqual([record.kind for record in records], [DecisionKind.ERROR])
        self.assertEqual(records[0].action, "run_shadow")

    def test_auto_execution_eligibility_requires_real_evidence_checkpoint_and_safe_apply(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "autonomy.db"
            seeded = seed_console_demo(db_path, Path(tmp) / "backups")
            proposal = PromptProposalStore(db_path).get(str(seeded["proposal_id"]))
            self.assertIsNotNone(proposal)
            assert proposal is not None
            PromptProposalStore(db_path).update_status(proposal.id, PromptProposalStatus.APPROVED)
            proposal.status = PromptProposalStatus.APPROVED
            shadow_store = ShadowResultStore(db_path)
            synthetic_shadow = ShadowResult(
                proposal_id=proposal.id,
                scenario_id=proposal.scenario_id,
                agent_id=proposal.agent_id,
                run_id="synthetic-shadow",
                status="success",
                passed=True,
                answer="synthetic",
                value_summary="synthetic evidence",
                run_kind="synthetic",
            )
            historical_shadow = ShadowResult(
                proposal_id=proposal.id,
                scenario_id=proposal.scenario_id,
                agent_id=proposal.agent_id,
                run_id="historical-shadow",
                status="success",
                passed=True,
                answer="historical",
                value_summary="historical evidence",
                comparison_result={"guardrail_violations": []},
                run_kind="historical",
            )
            shadow_store.save(synthetic_shadow)
            shadow_store.save(historical_shadow)
            capabilities = AdapterCapabilities(safe_apply=CapabilitySupport.SUPPORTED)

            synthetic = AutoExecutionEligibility().evaluate(
                proposal=proposal,
                shadow=synthetic_shadow,
                adapter_capabilities=capabilities,
                checkpoint_id="checkpoint-1",
                risk_score=0.2,
                patch_magnitude=0.05,
            )
            missing_checkpoint = AutoExecutionEligibility().evaluate(
                proposal=proposal,
                shadow=historical_shadow,
                adapter_capabilities=capabilities,
                checkpoint_id=None,
                risk_score=0.2,
                patch_magnitude=0.05,
            )
            eligible = AutoExecutionEligibility().evaluate(
                proposal=proposal,
                shadow=historical_shadow,
                adapter_capabilities=capabilities,
                checkpoint_id="checkpoint-1",
                risk_score=0.2,
                patch_magnitude=0.05,
            )

        self.assertFalse(synthetic.eligible)
        self.assertIn("synthetic_evidence", synthetic.reasons)
        self.assertFalse(missing_checkpoint.eligible)
        self.assertIn("missing_checkpoint", missing_checkpoint.reasons)
        self.assertTrue(eligible.eligible)
        self.assertEqual(eligible.reasons, ["eligible"])

    def test_autonomy_action_log_requires_checkpoint_and_tracks_rollback(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = AutonomyActionStore(Path(tmp) / "actions.db")

            with self.assertRaises(ValueError):
                store.create(
                    scenario_id="demo-quant",
                    proposal_id="proposal-1",
                    action_type="prompt_patch",
                    checkpoint_id="",
                    reason="Missing checkpoint should be rejected.",
                )
            action = store.create(
                scenario_id="demo-quant",
                proposal_id="proposal-1",
                action_type="prompt_patch",
                checkpoint_id="checkpoint-1",
                reason="Low-risk historical shadow passed.",
            )
            updated = store.update_status(
                action.id,
                AutonomyActionStatus.ROLLED_BACK,
                result={"rollback_reason": "operator drill"},
            )
            loaded = store.get(action.id)

            self.assertTrue(updated)
            self.assertIsNotNone(loaded)
            assert loaded is not None
            self.assertEqual(loaded.status, AutonomyActionStatus.ROLLED_BACK)
            self.assertEqual(loaded.result["rollback_reason"], "operator drill")

    @staticmethod
    def _client(db_path: Path, backup_dir: Path) -> tuple[TestClient, str]:
        manager = APIKeyManager()
        token = manager.generate_token("web")
        app = create_app(auth_manager=manager, db_path=db_path, backup_dir=backup_dir)
        return TestClient(app), token

    @staticmethod
    def _auth(token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}


if __name__ == "__main__":
    unittest.main()
