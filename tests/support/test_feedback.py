"""Feedback Collector tests."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from checkpoint_ai.experiment import Experiment, ExperimentLedger, ExperimentStatus
from checkpoint_ai.experiment.data_quality import DataQualityGate, QualityStatus
from checkpoint_ai.experiment.feedback import Feedback, FeedbackCollector, FeedbackSource
from tests.helpers import project_root


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

        root = project_root()
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

    def test_data_quality_gate_passes_warns_and_rejects_feedback(self) -> None:
        """DataQualityGate validates completeness, ranges, and confidence."""

        gate = DataQualityGate()
        passed = gate.validate(
            Feedback(
                experiment_id="experiment-1",
                source=FeedbackSource.INTERNAL,
                signal_type="latency",
                value=150.0,
            )
        )
        warned = gate.validate(
            Feedback(
                experiment_id="experiment-1",
                source=FeedbackSource.EXTERNAL,
                signal_type="ic_value",
                value=5.0,
            )
        )
        rejected = gate.validate(
            Feedback(
                experiment_id="experiment-1",
                source=FeedbackSource.MANUAL,
                signal_type="unknown",
                value="invalid",
            )
        )

        self.assertEqual(passed.status, QualityStatus.PASS)
        self.assertGreaterEqual(passed.confidence_score, gate.get_confidence_threshold())
        self.assertEqual(warned.status, QualityStatus.WARN)
        self.assertGreaterEqual(warned.confidence_score, gate.get_confidence_threshold())
        self.assertIn("out_of_range", warned.details)
        self.assertEqual(rejected.status, QualityStatus.REJECT)
        self.assertEqual(rejected.confidence_score, 0.0)
        self.assertIn("value must be numeric", rejected.issues)

    def test_collector_add_with_quality_stores_only_accepted_feedback(self) -> None:
        """Rejected feedback is recorded for audit but excluded from experiment metrics."""

        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "checkpoint_ai.db"
            ledger = ExperimentLedger(db_path)
            experiment = Experiment(
                business_line_id="quant",
                hypothesis="验证 IC 指标反馈质量。",
                action="factor_threshold=0.2",
                before_metrics={"ic_value": 0.1},
                status=ExperimentStatus.RUNNING,
            )
            experiment_id = ledger.create(experiment)
            collector = FeedbackCollector(db_path)

            accepted_id, accepted_quality = collector.add_with_quality(
                Feedback(
                    experiment_id=experiment_id,
                    source=FeedbackSource.EXTERNAL,
                    signal_type="ic_value",
                    value=0.2,
                )
            )
            rejected_id, rejected_quality = collector.add_with_quality(
                Feedback(
                    experiment_id=experiment_id,
                    source=FeedbackSource.EXTERNAL,
                    signal_type="ic_value",
                    value=5.0,
                )
            )
            stats = collector.get_quality_stats(experiment_id)
            result = collector.apply_to_experiment(experiment_id)
            rejected_items = collector.list_rejected_quality()

        self.assertEqual(accepted_quality.status, QualityStatus.PASS)
        self.assertEqual(rejected_quality.status, QualityStatus.WARN)
        self.assertNotEqual(accepted_id, rejected_id)
        self.assertEqual(stats["total"], 2)
        self.assertEqual(stats["pass"], 1)
        self.assertEqual(stats["warn"], 1)
        self.assertEqual(stats["reject"], 0)
        self.assertEqual(result["after_metrics"]["ic_value"], 5.0)
        self.assertEqual(rejected_items, [])

    def test_checkpointai_quality_cli_reports_stats_and_rejections(self) -> None:
        """CLI feedback add prints quality status and exposes rejected feedback."""

        root = project_root()
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

            pass_result = subprocess.run(
                [
                    "./checkpointai",
                    "--db",
                    str(db_path),
                    "experiment",
                    "feedback",
                    "add",
                    experiment_id,
                    "--source",
                    "internal",
                    "--type",
                    "latency",
                    "--value",
                    "150",
                ],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            reject_result = subprocess.run(
                [
                    "./checkpointai",
                    "--db",
                    str(db_path),
                    "experiment",
                    "feedback",
                    "add",
                    experiment_id,
                    "--source",
                    "manual",
                    "--type",
                    "unknown",
                    "--value",
                    "invalid",
                ],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            stats_result = subprocess.run(
                ["./checkpointai", "--db", str(db_path), "experiment", "quality", "stats", experiment_id],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            rejected_result = subprocess.run(
                ["./checkpointai", "--db", str(db_path), "experiment", "quality", "rejected"],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(pass_result.returncode, 0, pass_result.stderr)
        self.assertEqual(reject_result.returncode, 0, reject_result.stderr)
        self.assertEqual(stats_result.returncode, 0, stats_result.stderr)
        self.assertEqual(rejected_result.returncode, 0, rejected_result.stderr)
        self.assertIn("status=PASS", pass_result.stdout)
        self.assertIn("confidence=", pass_result.stdout)
        self.assertIn("status=REJECT", reject_result.stdout)
        self.assertIn('"reject": 1', stats_result.stdout)
        self.assertIn("unknown", rejected_result.stdout)


if __name__ == "__main__":
    unittest.main()
