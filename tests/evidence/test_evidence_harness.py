"""Tests for the clean Evidence Harness facade."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from loop_harness import EvidenceHarness
from loop_harness.evidence.models import DecisionRecommendation


def _payload(run_id: str, sharpe: float) -> dict[str, object]:
    return {
        "workflow_id": "quant_backtest_v1",
        "run_id": run_id,
        "run_kind": "historical",
        "nodes": [
            {"id": "load_data", "type": "data"},
            {"id": "strategy", "type": "agent"},
            {"id": "report", "type": "output"},
        ],
        "edges": [
            {"source": "load_data", "target": "strategy"},
            {"source": "strategy", "target": "report"},
        ],
        "trace": [
            {"node_id": "load_data", "status": "succeeded", "metrics": {"sample_count": 100}},
            {"node_id": "strategy", "status": "succeeded", "metrics": {"sharpe": sharpe}},
            {"node_id": "report", "status": "succeeded"},
        ],
        "metrics": {
            "sharpe": sharpe,
            "max_drawdown": 0.12,
            "sample_count": 100,
            "latency_ms": 300,
        },
        "metric_schema": {
            "sharpe": {"direction": "higher", "category": "business", "weight": 0.7},
            "max_drawdown": {
                "direction": "lower",
                "category": "guardrail",
                "weight": 0.3,
                "threshold": 0.2,
                "is_guardrail": True,
            },
            "sample_count": {"direction": "higher", "category": "data_quality", "weight": 0.0},
            "latency_ms": {"direction": "lower", "category": "system", "weight": 0.0},
        },
    }


class EvidenceHarnessTest(unittest.TestCase):
    """Validate the mainline facade stays independent of legacy platform plumbing."""

    def test_harness_ingests_visualizes_reports_and_compares_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            harness = EvidenceHarness(Path(tmp) / "evidence.db")

            baseline = harness.ingest_payload(_payload("baseline", 0.8))
            candidate = harness.ingest_payload(_payload("candidate", 1.2))
            visualization = harness.visualize("candidate")
            report = harness.report("candidate")
            comparison = harness.compare("baseline", "candidate")
            runs = harness.list_runs("quant_backtest_v1")

            self.assertEqual(baseline.run.run_id, "baseline")
            self.assertEqual(candidate.report.recommendation, DecisionRecommendation.CONTINUE_SHADOW)
            self.assertEqual(visualization.run_id, "candidate")
            self.assertEqual(report.run_id, "candidate")
            self.assertEqual(comparison.recommendation, DecisionRecommendation.APPROVE)
            self.assertEqual([run.run.run_id for run in runs], ["baseline", "candidate"])

    def test_harness_does_not_expose_legacy_runtime_platform_attributes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            harness = EvidenceHarness(Path(tmp) / "evidence.db")

            for attribute in ("agent_registry", "workflow", "tool_registry", "policy_engine", "human_gate"):
                with self.subTest(attribute=attribute):
                    self.assertFalse(hasattr(harness, attribute))


if __name__ == "__main__":
    unittest.main()
