"""Evidence comparison to approval proposal tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from checkpoint_ai import CheckpointAI
from checkpoint_ai.api import create_app
from checkpoint_ai.auth import APIKeyManager


class EvidenceToProposalTest(unittest.TestCase):
    """Improved trusted evidence should create a reviewable proposal."""

    def test_api_creates_approval_proposal_from_improved_comparison(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "proposal.db"
            client, token = self._client(db_path)
            headers = self._auth(token)
            client.post("/api/evidence/runs", json=_payload("baseline", 0.8, "historical", 100), headers=headers)
            client.post("/api/evidence/runs", json=_payload("candidate", 1.2, "historical", 100), headers=headers)

            created = client.post(
                "/api/evidence/proposals",
                json={
                    "baseline_run_id": "baseline",
                    "candidate_run_id": "candidate",
                    "scenario_id": "quant",
                },
                headers=headers,
            )
            approvals = client.get("/api/approvals?scenario_id=quant", headers=headers)

        self.assertEqual(created.status_code, 200)
        self.assertEqual(created.json()["proposal_kind"], "evidence")
        self.assertEqual(created.json()["metadata"]["baseline_run_id"], "baseline")
        self.assertEqual(created.json()["metadata"]["candidate_run_id"], "candidate")
        self.assertEqual(approvals.status_code, 200)
        self.assertEqual(approvals.json()[0]["source_id"], created.json()["id"])
        self.assertEqual(approvals.json()[0]["item_type"], "evidence_proposal")

    def test_api_refuses_rejected_quality_evidence_proposal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "proposal.db"
            client, token = self._client(db_path)
            headers = self._auth(token)
            client.post("/api/evidence/runs", json=_payload("baseline", 0.8, "historical", 100), headers=headers)
            client.post("/api/evidence/runs", json=_payload("candidate", 1.2, "synthetic", 5), headers=headers)

            created = client.post(
                "/api/evidence/proposals",
                json={
                    "baseline_run_id": "baseline",
                    "candidate_run_id": "candidate",
                    "scenario_id": "quant",
                },
                headers=headers,
            )

        self.assertEqual(created.status_code, 400)
        self.assertEqual(created.json()["code"], "evidence.proposal_not_allowed")

    @staticmethod
    def _client(db_path: Path) -> tuple[TestClient, str]:
        manager = APIKeyManager()
        token = manager.generate_token("web")
        app = create_app(
            checkpoint_ai=CheckpointAI(sqlite_path=db_path),
            auth_manager=manager,
            db_path=db_path,
        )
        return TestClient(app), token

    @staticmethod
    def _auth(token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}


def _payload(run_id: str, sharpe: float, run_kind: str, sample_count: int) -> dict[str, object]:
    trace = [{"node_id": "strategy", "status": "succeeded", "metrics": {"sharpe": sharpe}}]
    return {
        "workflow_id": "quant_backtest_v1",
        "run_id": run_id,
        "run_kind": run_kind,
        "nodes": [{"id": "strategy", "type": "agent"}],
        "trace": trace,
        "metrics": {"sharpe": sharpe, "max_drawdown": 0.12, "sample_count": sample_count},
        "metric_schema": {
            "sharpe": {"direction": "higher", "category": "business", "weight": 0.7},
            "max_drawdown": {"direction": "lower", "category": "business", "weight": 0.3},
            "sample_count": {"direction": "higher", "category": "data_quality", "weight": 0.0},
        },
    }


if __name__ == "__main__":
    unittest.main()
