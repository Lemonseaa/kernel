"""Feedback Collector tests."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from checkpoint_ai.experiment import Experiment, ExperimentLedger, ExperimentStatus
from checkpoint_ai.experiment.feedback import Feedback, FeedbackCollector, FeedbackSource


class FeedbackCollectorTest(unittest.TestCase):
    """Validate V1.2 Feedback Collector behavior."""

    def test_collector_adds_lists_and_applies_feedback_to_experiment(self) -> None:
        """Feedback is persisted, associated to an experiment, and updates after_metrics."""

        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "checkpoint_ai.db"
            ledger = ExperimentLedger(db_path)
            experiment = Experiment(
                business_line_id="content",
                hypothesis="测试标题长度变化。",
                action="title_length=-20%",
                before_metrics={"engagement": 10.0},
                status=ExperimentStatus.RUNNING,
            )
            experiment_id = ledger.create(experiment)
            collector = FeedbackCollector(db_path)

            feedback_id = collector.add(
                Feedback(
                    experiment_id=experiment_id,
                    source=FeedbackSource.EXTERNAL,
                    signal_type="engagement",
                    value=12.5,
                    context={"platform": "xiaohongshu"},
                )
            )
            feedback = collector.list(experiment_id=experiment_id)
            result = collector.apply_to_experiment(experiment_id)
            updated = ledger.get(experiment_id)

        self.assertEqual(len(feedback), 1)
        self.assertEqual(feedback[0].id, feedback_id)
        self.assertEqual(feedback[0].source, FeedbackSource.EXTERNAL)
        self.assertEqual(result["metrics"]["engagement"]["delta"], 2.5)
        self.assertIsNotNone(updated)
        self.assertEqual(updated.after_metrics["engagement"], 12.5)
        self.assertIn("engagement", updated.result_summary)

    def test_checkpointai_feedback_cli_add_list_and_result(self) -> None:
        """CLI can add feedback, list feedback, and calculate experiment result."""

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
            ids = [
                line.split(":", 1)[1].strip()
                for line in demo.stdout.splitlines()
                if line.startswith("Experiment ID:")
            ]
            experiment_id = ids[1]

            add_result = subprocess.run(
                [
                    "./checkpointai",
                    "--db",
                    str(db_path),
                    "experiment",
                    "feedback",
                    "add",
                    experiment_id,
                    "--source",
                    "external",
                    "--type",
                    "engagement",
                    "--value",
                    "13.0",
                ],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            list_result = subprocess.run(
                ["./checkpointai", "--db", str(db_path), "experiment", "feedback", "list", experiment_id],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            result = subprocess.run(
                ["./checkpointai", "--db", str(db_path), "experiment", "result", experiment_id],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(add_result.returncode, 0, add_result.stderr)
        self.assertEqual(list_result.returncode, 0, list_result.stderr)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Feedback ID:", add_result.stdout)
        self.assertIn("external", list_result.stdout)
        self.assertIn("engagement", result.stdout)
        self.assertIn("delta", result.stdout)


if __name__ == "__main__":
    unittest.main()
