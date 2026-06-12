"""Evidence workflow baseline tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from checkpoint_ai import CheckpointAI
from checkpoint_ai.api import create_app
from checkpoint_ai.auth import APIKeyManager
from checkpoint_ai.evidence.baseline_store import EvidenceBaselineStore


class EvidenceBaselineTest(unittest.TestCase):
    """Workflow baselines should persist and feed comparison defaults."""

    def test_baseline_store_saves_and_loads_workflow_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = EvidenceBaselineStore(Path(tmp) / "baseline.db")
            record = store.set_baseline(
                workflow_id="quant",
                baseline_run_id="run-a",
                reason="Stable historical baseline.",
            )
            loaded = store.get_baseline("quant")

        self.assertEqual(record.workflow_id, "quant")
        self.assertEqual(loaded.baseline_run_id if loaded else None, "run-a")
        self.assertEqual(loaded.reason if loaded else None, "Stable historical baseline.")

    def test_api_sets_gets_and_uses_default_baseline_for_compare(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "baseline.db"
            client, token = self._client(db_path)
            headers = self._auth(token)
            client.post("/api/evidence/runs", json=_payload("baseline", 0.8), headers=headers)
            client.post("/api/evidence/runs", json=_payload("candidate", 1.2), headers=headers)

            set_baseline = client.post(
                "/api/evidence/workflows/quant_backtest_v1/baseline",
                json={"baseline_run_id": "baseline", "reason": "Known stable run."},
                headers=headers,
            )
            get_baseline = client.get("/api/evidence/workflows/quant_backtest_v1/baseline", headers=headers)
            comparison = client.post(
                "/api/evidence/compare",
                json={"candidate_run_id": "candidate"},
                headers=headers,
            )

        self.assertEqual(set_baseline.status_code, 200)
        self.assertEqual(set_baseline.json()["baseline_run_id"], "baseline")
        self.assertEqual(get_baseline.status_code, 200)
        self.assertEqual(get_baseline.json()["baseline_run_id"], "baseline")
        self.assertEqual(comparison.status_code, 200)
        self.assertEqual(comparison.json()["baseline_run_id"], "baseline")
        self.assertEqual(comparison.json()["candidate_run_id"], "candidate")

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


def _payload(run_id: str, sharpe: float) -> dict[str, object]:
    return {
        "workflow_id": "quant_backtest_v1",
        "run_id": run_id,
        "run_kind": "historical",
        "nodes": [{"id": "strategy", "type": "agent"}],
        "trace": [{"node_id": "strategy", "status": "succeeded", "metrics": {"sharpe": sharpe}}],
        "metrics": {"sharpe": sharpe, "max_drawdown": 0.12, "sample_count": 100},
        "metric_schema": {
            "sharpe": {"direction": "higher", "category": "business", "weight": 0.7},
            "max_drawdown": {"direction": "lower", "category": "business", "weight": 0.3},
            "sample_count": {"direction": "higher", "category": "data_quality", "weight": 0.0},
        },
    }


if __name__ == "__main__":
    unittest.main()
