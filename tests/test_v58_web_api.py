"""V5.8 Web API contract tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from checkpoint_ai import CheckpointAI
from checkpoint_ai.api import create_app
from checkpoint_ai.auth import APIKeyManager
from checkpoint_ai.console import BackupManager, CostEvent, CostEventStore
from checkpoint_ai.prompt import (
    PromptPatch,
    PromptProposal,
    PromptProposalStore,
    PromptSlot,
)
from checkpoint_ai.scenario import Scenario, ScenarioStore


class V58WebApiTest(unittest.TestCase):
    """Validate the P0 Web API contract consumed by the React console."""

    def test_console_api_requires_auth_and_returns_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "web.db"
            self._create_scenario(db_path)
            client, token = self._client(db_path)

            unauthorized = client.get("/api/console/snapshot?scenario_id=quant")
            authorized = client.get(
                "/api/console/snapshot?scenario_id=quant",
                headers=self._auth(token),
            )

        self.assertEqual(unauthorized.status_code, 401)
        self.assertEqual(authorized.status_code, 200)
        self.assertEqual(authorized.json()["scope"]["scenario_id"], "quant")
        self.assertEqual(authorized.json()["scenario_count"], 1)

    def test_approvals_can_be_listed_viewed_approved_and_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "web.db"
            proposal_id = self._create_prompt_proposal(db_path)
            client, token = self._client(db_path)

            listing = client.get("/api/approvals?scenario_id=quant", headers=self._auth(token))
            detail = client.get(f"/api/approvals/{proposal_id}", headers=self._auth(token))
            approve = client.post(
                f"/api/approvals/{proposal_id}/approve",
                json={"comment": "Evidence is enough for this demo."},
                headers=self._auth(token),
            )
            reject = client.post(
                f"/api/approvals/{proposal_id}/reject",
                json={"comment": "Reject after review."},
                headers=self._auth(token),
            )

        self.assertEqual(listing.status_code, 200)
        self.assertEqual(listing.json()[0]["source_id"], proposal_id)
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["item_type"], "prompt_proposal")
        self.assertEqual(detail.json()["detail"]["patch"]["after"], "json")
        self.assertEqual(approve.status_code, 200)
        self.assertTrue(approve.json()["updated"])
        self.assertEqual(reject.status_code, 200)
        self.assertTrue(reject.json()["updated"])

    def test_runs_scenarios_adapters_backups_and_health_are_exposed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            db_path = root / "web.db"
            self._create_scenario(db_path)
            CostEventStore(db_path).record(
                CostEvent(
                    scenario_id="quant",
                    business_line_id="trading",
                    provider="minimax",
                    input_tokens=20,
                    output_tokens=10,
                    estimated_cost=0.03,
                )
            )
            backup = BackupManager(db_path, root / "backups").create_backup(label="before-api")
            client, token = self._client(db_path, backup_dir=root / "backups")
            headers = self._auth(token)

            scenarios = client.get("/api/scenarios", headers=headers)
            adapters = client.get("/api/adapters", headers=headers)
            run = client.post(
                "/api/runs",
                json={"scenario_id": "quant", "task": "analyze_signal", "context": {"symbol": "AAPL"}},
                headers=headers,
            )
            runs = client.get("/api/runs?scenario_id=quant", headers=headers)
            run_detail = client.get(f"/api/runs/{run.json()['run_id']}", headers=headers)
            backups = client.get("/api/backups", headers=headers)
            restore = client.post(f"/api/backups/{backup.id}/restore", headers=headers)
            health = client.get("/api/health", headers=headers)

        self.assertEqual(scenarios.status_code, 200)
        self.assertEqual(scenarios.json()[0]["id"], "quant")
        self.assertEqual(adapters.status_code, 200)
        self.assertTrue(any(adapter["name"] == "dummy_stock_signal" for adapter in adapters.json()))
        self.assertEqual(run.status_code, 200)
        self.assertEqual(run.json()["status"], "success")
        self.assertEqual(runs.status_code, 200)
        self.assertEqual(runs.json()[0]["scenario_id"], "quant")
        self.assertEqual(run_detail.status_code, 200)
        self.assertEqual(run_detail.json()["run_id"], run.json()["run_id"])
        self.assertEqual(backups.status_code, 200)
        self.assertEqual(backups.json()[0]["label"], "before-api")
        self.assertEqual(restore.status_code, 200)
        self.assertTrue(restore.json()["restored"])
        self.assertEqual(health.status_code, 200)
        self.assertIn("overall_status", health.json())

    def test_fallback_routes_include_console_api_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "web.db"
            app = create_app(
                checkpoint_ai=CheckpointAI(sqlite_path=db_path),
                auth_manager=APIKeyManager(),
                db_path=db_path,
                force_fallback=True,
            )

        paths = {route["path"] for route in app.routes}
        self.assertIn("/api/console/snapshot", paths)
        self.assertIn("/api/approvals", paths)
        self.assertIn("/api/backups", paths)

    @staticmethod
    def _client(db_path: Path, backup_dir: Path | None = None) -> tuple[TestClient, str]:
        manager = APIKeyManager()
        token = manager.generate_token("web")
        app = create_app(
            checkpoint_ai=CheckpointAI(sqlite_path=db_path),
            auth_manager=manager,
            db_path=db_path,
            backup_dir=backup_dir,
        )
        return TestClient(app), token

    @staticmethod
    def _auth(token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    @staticmethod
    def _create_scenario(db_path: Path) -> None:
        ScenarioStore(db_path).save(
            Scenario(
                id="quant",
                name="Quant",
                description="Web API scenario",
                adapter_type="dummy_stock_signal",
                metadata={"domain_tags": ["quant"]},
            )
        )

    @staticmethod
    def _create_prompt_proposal(db_path: Path) -> str:
        proposal = PromptProposal(
            scenario_id="quant",
            agent_id="researcher",
            patch=PromptPatch(
                slot=PromptSlot.OUTPUT_FORMAT,
                operation="replace",
                before="text",
                after="json",
            ),
            reason="Improve structured evaluation.",
            expected_metric="sharpe",
        )
        PromptProposalStore(db_path).create(proposal)
        return proposal.id


if __name__ == "__main__":
    unittest.main()
