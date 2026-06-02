"""Experiment Ledger MVP tests."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from checkpoint_ai.experiment import Experiment, ExperimentLedger, ExperimentStatus


class ExperimentLedgerTest(unittest.TestCase):
    """Validate V1.1 Experiment Ledger behavior."""

    def test_ledger_creates_updates_lists_compares_and_summarizes_experiments(self) -> None:
        """The ledger records experiment lifecycle and answers the seven questions."""

        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "checkpoint_ai.db"
            ledger = ExperimentLedger(db_path)
            baseline = Experiment(
                business_line_id="content",
                hypothesis="建立当前标题策略的基线。",
                action="baseline",
                before_metrics={"engagement": 10.0},
                after_metrics={"engagement": 10.0},
                result_summary="基线已记录。",
                status=ExperimentStatus.COMPLETED,
            )
            challenger = Experiment(
                business_line_id="content",
                hypothesis="测试更短标题是否提高互动率。",
                baseline_id=baseline.id,
                action="title_length=-20%",
                before_metrics={"engagement": 10.0},
                after_metrics={"engagement": 12.5},
                result_summary="互动率提升。",
                status=ExperimentStatus.COMPLETED,
            )

            baseline_id = ledger.create(baseline)
            challenger_id = ledger.create(challenger)
            updated = ledger.update(challenger_id, metadata={"owner": "demo"})

            loaded = ledger.get(challenger_id)
            listed = ledger.list(business_line_id="content", status=ExperimentStatus.COMPLETED)
            comparison = ledger.compare(baseline_id, challenger_id)
            summary = ledger.generate_summary(challenger_id)

        self.assertTrue(updated)
        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.metadata["owner"], "demo")
        self.assertEqual(len(listed), 2)
        self.assertEqual(comparison["metrics"]["engagement"]["delta"], 2.5)
        self.assertIn("为什么做这个实验？", summary)
        self.assertIn("基线是什么？", summary)
        self.assertIn("有没有变好？", summary)
        self.assertIn(challenger_id, summary)

    def test_checkpointai_experiment_cli_run_demo_list_show_and_compare(self) -> None:
        """The CLI exposes demo, list, show, and compare commands."""

        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "checkpoint_ai.db"
            demo = subprocess.run(
                ["./checkpointai", "--db", str(db_path), "experiment", "run-demo"],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(demo.returncode, 0, demo.stderr)
            self.assertIn("为什么做这个实验？", demo.stdout)

            ids = [
                line.split(":", 1)[1].strip()
                for line in demo.stdout.splitlines()
                if line.startswith("Experiment ID:")
            ]
            self.assertEqual(len(ids), 2)

            list_result = subprocess.run(
                ["./checkpointai", "--db", str(db_path), "experiment", "list"],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            show_result = subprocess.run(
                ["./checkpointai", "--db", str(db_path), "experiment", "show", ids[1]],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            compare_result = subprocess.run(
                ["./checkpointai", "--db", str(db_path), "experiment", "compare", ids[0], ids[1]],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(list_result.returncode, 0, list_result.stderr)
        self.assertEqual(show_result.returncode, 0, show_result.stderr)
        self.assertEqual(compare_result.returncode, 0, compare_result.stderr)
        self.assertIn("title_length=-20%", list_result.stdout)
        self.assertIn("为什么做这个实验？", show_result.stdout)
        self.assertIn("engagement", compare_result.stdout)


if __name__ == "__main__":
    unittest.main()
