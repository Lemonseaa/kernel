"""Experiment Ledger MVP tests."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path

from loop_harness.experiment import (
    ActionRisk,
    BaselineManager,
    Experiment,
    ExperimentLedger,
    ExperimentStatus,
    LoopEngine,
    RiskScorer,
    SimpleComparer,
    TickStatus,
)
from tests.helpers import project_root


class ExperimentLedgerTest(unittest.TestCase):
    """Validate V1.1 Experiment Ledger behavior."""

    def test_ledger_creates_updates_lists_compares_and_summarizes_experiments(self) -> None:
        """The ledger records experiment lifecycle and answers the seven questions."""

        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "loop_harness.db"
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

    def test_loopharness_experiment_cli_run_demo_list_show_and_compare(self) -> None:
        """The CLI exposes demo, list, show, and compare commands."""

        root = project_root()
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "loop_harness.db"
            demo = subprocess.run(
                ["./loopharness", "--db", str(db_path), "experiment", "run-demo"],
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
                ["./loopharness", "--db", str(db_path), "experiment", "list"],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            show_result = subprocess.run(
                ["./loopharness", "--db", str(db_path), "experiment", "show", ids[1]],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            compare_result = subprocess.run(
                ["./loopharness", "--db", str(db_path), "experiment", "compare", ids[0], ids[1]],
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

    def test_baseline_manager_tracks_active_baseline_per_business_line(self) -> None:
        """BaselineManager creates, lists, and activates baselines."""

        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "loop_harness.db"
            manager = BaselineManager(db_path)

            first_id = manager.create({"latency": 100.0}, name="content-v1", business_line_id="content")
            second_id = manager.create({"latency": 85.0}, name="content-v2", business_line_id="content")
            quant_id = manager.create({"ic_value": 0.1}, name="quant-v1", business_line_id="quant")
            manager.set_active(first_id)

            content_active = manager.get_active("content")
            quant_active = manager.get_active("quant")
            content_baselines = manager.list("content")

        self.assertIsNotNone(content_active)
        self.assertIsNotNone(quant_active)
        self.assertEqual(content_active.id, first_id)
        self.assertEqual(quant_active.id, quant_id)
        self.assertEqual(len(content_baselines), 2)
        self.assertIn(second_id, {baseline.id for baseline in content_baselines})

    def test_simple_comparer_compares_experiment_with_active_baseline(self) -> None:
        """SimpleComparer compares metrics and marks a stronger experiment as winner."""

        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "loop_harness.db"
            manager = BaselineManager(db_path)
            manager.create(
                {"latency": 100.0, "success_rate": 0.95},
                name="ops-baseline",
                business_line_id="ops",
            )
            ledger = ExperimentLedger(db_path)
            experiment = Experiment(
                business_line_id="ops",
                hypothesis="降低延迟并保持成功率。",
                action="provider_timeout=-15%",
                before_metrics={"latency": 100.0, "success_rate": 0.95},
                after_metrics={"latency": 85.0, "success_rate": 0.97},
                result_summary="延迟降低，成功率提高。",
                status=ExperimentStatus.COMPLETED,
            )
            experiment_id = ledger.create(experiment)

            result = SimpleComparer(db_path).compare(experiment_id)
            ledger_result = ledger.compare_to_baseline(experiment_id)

        self.assertEqual(result.winner, "experiment")
        self.assertEqual(result.delta["latency"], -15.0)
        self.assertAlmostEqual(result.improvement["success_rate"], 0.0210526315)
        self.assertTrue(SimpleComparer(db_path).is_better(result))
        self.assertEqual(ledger_result.winner, "experiment")

    def test_ledger_can_promote_experiment_to_baseline(self) -> None:
        """ExperimentLedger can turn an experiment result into the active baseline."""

        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "loop_harness.db"
            ledger = ExperimentLedger(db_path)
            experiment = Experiment(
                business_line_id="content",
                hypothesis="测试新模板。",
                action="template=hook-first",
                before_metrics={"engagement": 10.0},
                after_metrics={"engagement": 13.0},
                result_summary="互动率提升。",
                status=ExperimentStatus.COMPLETED,
            )
            experiment_id = ledger.create(experiment)

            baseline_id = ledger.set_baseline(experiment_id)
            active = BaselineManager(db_path).get_active("content")

        self.assertIsNotNone(active)
        self.assertEqual(active.id, baseline_id)
        self.assertEqual(active.experiment_id, experiment_id)
        self.assertEqual(active.metrics["engagement"], 13.0)

    def test_loopharness_baseline_cli_create_compare_and_promote(self) -> None:
        """CLI exposes baseline management and experiment baseline comparison."""

        root = project_root()
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "loop_harness.db"
            create_result = subprocess.run(
                [
                    "./loopharness",
                    "--db",
                    str(db_path),
                    "baseline",
                    "create",
                    "--metrics",
                    '{"engagement": 10.0}',
                    "--name",
                    "demo-baseline",
                    "--business-line-id",
                    "demo",
                ],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            demo = subprocess.run(
                ["./loopharness", "--db", str(db_path), "experiment", "run-demo"],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            ids = [
                line.split(":", 1)[1].strip()
                for line in demo.stdout.splitlines()
                if line.startswith("Experiment ID:")
            ]
            experiment_id = ids[1]
            compare_result = subprocess.run(
                ["./loopharness", "--db", str(db_path), "experiment", "compare-baseline", experiment_id],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            promote_result = subprocess.run(
                ["./loopharness", "--db", str(db_path), "experiment", "promote", experiment_id],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            list_result = subprocess.run(
                ["./loopharness", "--db", str(db_path), "baseline", "list"],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(create_result.returncode, 0, create_result.stderr)
        self.assertEqual(demo.returncode, 0, demo.stderr)
        self.assertEqual(compare_result.returncode, 0, compare_result.stderr)
        self.assertEqual(promote_result.returncode, 0, promote_result.stderr)
        self.assertEqual(list_result.returncode, 0, list_result.stderr)
        self.assertIn("Baseline ID:", create_result.stdout)
        self.assertIn("winner", compare_result.stdout)
        self.assertIn("Baseline ID:", promote_result.stdout)
        self.assertIn("demo-baseline", list_result.stdout)

    def test_risk_scorer_scores_low_and_high_risk_actions(self) -> None:
        """RiskScorer calculates weighted risk and review requirement."""

        scorer = RiskScorer()
        low_risk = scorer.score_action(
            ActionRisk(
                action_type="parameter_tune",
                target="timeout",
                magnitude=0.1,
                reversibility=0.9,
                confidence=0.9,
                policy_compliant=True,
            )
        )
        high_risk = scorer.score_action(
            ActionRisk(
                action_type="strategy_switch",
                target="backtest_strategy",
                magnitude=0.8,
                reversibility=0.2,
                confidence=0.6,
                policy_compliant=True,
            )
        )

        self.assertAlmostEqual(low_risk.total, 0.15)
        self.assertFalse(low_risk.requires_human_review)
        self.assertTrue(scorer.should_auto_execute(low_risk))
        self.assertAlmostEqual(high_risk.total, 0.65)
        self.assertTrue(high_risk.requires_human_review)
        self.assertFalse(scorer.should_auto_execute(high_risk))
        self.assertIn("magnitude", high_risk.report)

    def test_ledger_scores_experiment_risk_from_metadata(self) -> None:
        """ExperimentLedger can score risk from experiment metadata."""

        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "loop_harness.db"
            ledger = ExperimentLedger(db_path)
            experiment = Experiment(
                business_line_id="ops",
                hypothesis="切换回测策略。",
                action="strategy_switch: backtest_strategy",
                before_metrics={"success_rate": 0.9},
                after_metrics={"success_rate": 0.92},
                result_summary="策略表现略好。",
                status=ExperimentStatus.COMPLETED,
                metadata={
                    "action_type": "strategy_switch",
                    "target": "backtest_strategy",
                    "magnitude": 0.8,
                    "reversibility": 0.2,
                    "confidence": 0.6,
                    "policy_compliant": True,
                },
            )
            experiment_id = ledger.create(experiment)

            risk = ledger.score_risk(experiment_id)

        self.assertAlmostEqual(risk.total, 0.65)
        self.assertTrue(risk.requires_human_review)

    def test_loopharness_risk_cli_scores_actions_and_experiments(self) -> None:
        """CLI exposes action and experiment risk scoring."""

        root = project_root()
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "loop_harness.db"
            low_result = subprocess.run(
                [
                    "./loopharness",
                    "--db",
                    str(db_path),
                    "risk",
                    "score",
                    "--type",
                    "parameter_tune",
                    "--target",
                    "timeout",
                    "--magnitude",
                    "0.1",
                    "--reversibility",
                    "0.9",
                    "--confidence",
                    "0.9",
                ],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            high_result = subprocess.run(
                [
                    "./loopharness",
                    "--db",
                    str(db_path),
                    "risk",
                    "score",
                    "--type",
                    "strategy_switch",
                    "--target",
                    "backtest_strategy",
                    "--magnitude",
                    "0.8",
                    "--reversibility",
                    "0.2",
                    "--confidence",
                    "0.6",
                ],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            demo = subprocess.run(
                ["./loopharness", "--db", str(db_path), "experiment", "run-demo"],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            ids = [
                line.split(":", 1)[1].strip()
                for line in demo.stdout.splitlines()
                if line.startswith("Experiment ID:")
            ]
            experiment_result = subprocess.run(
                ["./loopharness", "--db", str(db_path), "experiment", "risk", ids[1]],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(low_result.returncode, 0, low_result.stderr)
        self.assertEqual(high_result.returncode, 0, high_result.stderr)
        self.assertEqual(demo.returncode, 0, demo.stderr)
        self.assertEqual(experiment_result.returncode, 0, experiment_result.stderr)
        self.assertIn('"total": 0.15', low_result.stdout)
        self.assertIn('"requires_human_review": false', low_result.stdout)
        self.assertIn('"total": 0.65', high_result.stdout)
        self.assertIn('"requires_human_review": true', high_result.stdout)
        self.assertIn("magnitude_risk", experiment_result.stdout)

    def test_loop_engine_runs_tick_and_persists_history(self) -> None:
        """LoopEngine runs an explainable tick and stores it in SQLite."""

        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "loop_harness.db"
            engine = LoopEngine.default(db_path)

            tick = engine.tick(reason="manual test tick", business_line_id="content")
            status = engine.get_status("content")
            last_tick = engine.get_last_tick()
            history = engine.history(limit=5)
            experiment = ExperimentLedger(db_path).get(tick.experiment_id)

        self.assertEqual(tick.status, TickStatus.CHECKPOINTED)
        self.assertGreaterEqual(tick.duration_ms, 0)
        self.assertIn("manual test tick", tick.summary)
        self.assertEqual(status["last_tick_id"], tick.id)
        self.assertIsNotNone(last_tick)
        self.assertEqual(last_tick.id, tick.id)
        self.assertEqual(len(history), 1)
        self.assertIsNotNone(experiment)
        self.assertIn("loop_tick_id", experiment.metadata)

    def test_loop_engine_pause_resume_stop_and_trigger(self) -> None:
        """LoopEngine supports lifecycle controls and event-triggered ticks."""

        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "loop_harness.db"
            engine = LoopEngine.default(db_path)
            completed: list[str] = []
            errors: list[str] = []
            engine.on_tick_complete(lambda tick: completed.append(tick.id))
            engine.on_error(lambda error: errors.append(str(error)))

            start_tick = engine.start(tick_interval=5)
            engine.pause()
            paused_status = engine.get_status()
            skipped_tick = engine.trigger("feedback.received", {"value": 1})
            engine.resume()
            resumed_tick = engine.trigger("feedback.received", {"value": 2})
            engine.stop()
            stopped_status = engine.get_status()

        self.assertEqual(start_tick.status, TickStatus.CHECKPOINTED)
        self.assertEqual(paused_status["state"], "paused")
        self.assertIsNone(skipped_tick)
        self.assertIsNotNone(resumed_tick)
        self.assertEqual(stopped_status["state"], "stopped")
        self.assertEqual(len(completed), 2)
        self.assertEqual(errors, [])

    def test_loopharness_loop_cli_controls_and_reports_ticks(self) -> None:
        """CLI exposes loop lifecycle and tick inspection commands."""

        root = project_root()
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "loop_harness.db"
            start_result = subprocess.run(
                ["./loopharness", "--db", str(db_path), "loop", "start"],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            status_result = subprocess.run(
                ["./loopharness", "--db", str(db_path), "loop", "status"],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            history_result = subprocess.run(
                ["./loopharness", "--db", str(db_path), "loop", "history", "--limit", "5"],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            last_tick_result = subprocess.run(
                ["./loopharness", "--db", str(db_path), "loop", "last-tick"],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            stop_result = subprocess.run(
                ["./loopharness", "--db", str(db_path), "loop", "stop"],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(start_result.returncode, 0, start_result.stderr)
        self.assertEqual(status_result.returncode, 0, status_result.stderr)
        self.assertEqual(history_result.returncode, 0, history_result.stderr)
        self.assertEqual(last_tick_result.returncode, 0, last_tick_result.stderr)
        self.assertEqual(stop_result.returncode, 0, stop_result.stderr)
        self.assertIn("Loop started", start_result.stdout)
        self.assertIn("running", status_result.stdout)
        self.assertIn("checkpointed", history_result.stdout)
        self.assertIn("summary", last_tick_result.stdout)
        self.assertIn("Loop stopped", stop_result.stdout)


if __name__ == "__main__":
    unittest.main()
