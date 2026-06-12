"""Evidence drill script tests."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from checkpoint_ai.evidence import EvidenceBaselineStore, EvidenceStore
from checkpoint_ai.prompt import ProposalStore


class EvidenceDrillScriptTest(unittest.TestCase):
    """The evidence drill should generate enough state for UI validation."""

    def test_drill_script_creates_runs_baseline_and_proposal(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "drill.db"
            completed = subprocess.run(
                [
                    sys.executable,
                    "scripts/business_lines/run_evidence_drill.py",
                    "--db",
                    str(db_path),
                    "--candidates",
                    "10",
                ],
                cwd=Path(__file__).parents[3],
                check=True,
                capture_output=True,
                text=True,
            )
            runs = EvidenceStore(db_path).list_runs(workflow_id="quant_backtest_v1")
            baseline = EvidenceBaselineStore(db_path).get_baseline("quant_backtest_v1")
            proposals = ProposalStore(db_path).list(scenario_id="quant")

        self.assertIn("evidence_drill_summary", completed.stdout)
        self.assertIn("run_count=11", completed.stdout)
        self.assertEqual(len(runs), 11)
        self.assertEqual(baseline.baseline_run_id if baseline else None, "quant_baseline_drill")
        self.assertEqual(len(proposals), 1)
        self.assertEqual(proposals[0].proposal_kind.value, "evidence")


if __name__ == "__main__":
    unittest.main()
