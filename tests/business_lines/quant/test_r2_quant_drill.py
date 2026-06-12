"""R2 quant backtest drill tests."""

from __future__ import annotations

import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from loop_harness.evidence import EvidenceService, EvidenceStore
from loop_harness.evidence.quant_drill import QuantDrillRunner


class R2QuantDrillTest(unittest.TestCase):
    """Validate the quant evidence drill against semi-real historical runs."""

    def test_quant_drill_creates_runs_comparisons_and_review_summary(self) -> None:
        """The drill should create enough evidence to judge candidate quality."""
        with tempfile.TemporaryDirectory() as tmp:
            service = EvidenceService(EvidenceStore(Path(tmp) / "evidence.db"))
            result = QuantDrillRunner(service).run(candidate_count=30, comparison_count=5)

            self.assertEqual(result.workflow_id, "quant_backtest_v1")
            self.assertEqual(result.run_count, 31)
            self.assertEqual(result.candidate_count, 30)
            self.assertEqual(len(result.comparisons), 5)
            self.assertGreaterEqual(result.report_count, 6)
            self.assertGreaterEqual(len(result.system_findings), 3)
            self.assertIn(result.paper_trade_recommendation, {"enter_paper", "continue_shadow", "reject"})
            self.assertIn("return_delta", result.review)
            self.assertIn("drawdown_delta", result.review)
            self.assertIn("sample_sufficient", result.review)
            self.assertIn("overfit_risk", result.review)
            self.assertEqual(len(service.store.list_runs("quant_backtest_v1")), 31)
            self.assertEqual(len(service.store.list_comparison_reports("quant_backtest_v1")), 5)

    def test_quant_drill_cli_outputs_human_relevant_summary(self) -> None:
        """CLI users should see whether the evidence is enough for paper trading."""
        from loop_harness.cli import main

        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "evidence.db"

            output = StringIO()
            with redirect_stdout(output):
                status = main([
                    "--db",
                    str(db_path),
                    "evidence",
                    "quant-drill",
                    "--candidates",
                    "30",
                    "--comparisons",
                    "5",
                ])

            self.assertEqual(status, 0)
            self.assertIn("paper_trade_recommendation", output.getvalue())
            service = EvidenceService(EvidenceStore(db_path))
            self.assertEqual(len(service.store.list_runs("quant_backtest_v1")), 31)
            self.assertEqual(len(service.store.list_comparison_reports("quant_backtest_v1")), 5)


if __name__ == "__main__":
    unittest.main()
