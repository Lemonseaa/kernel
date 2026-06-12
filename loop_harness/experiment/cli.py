"""CLI commands for Experiment Ledger."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from loop_harness.experiment.baseline import BaselineManager
from loop_harness.experiment.feedback import Feedback, FeedbackCollector, FeedbackSource
from loop_harness.experiment.ledger import ExperimentLedger
from loop_harness.experiment.loop_engine import LoopEngine, Tick
from loop_harness.experiment.models import Experiment, ExperimentStatus
from loop_harness.experiment.risk_score import ActionRisk, RiskScorer


def register_experiment_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register experiment subcommands."""

    experiment_parser = subparsers.add_parser("experiment")
    experiment_subparsers = experiment_parser.add_subparsers(dest="experiment_command")
    experiment_subparsers.add_parser("run-demo")
    experiment_subparsers.add_parser("list")
    show_parser = experiment_subparsers.add_parser("show")
    show_parser.add_argument("id")
    compare_parser = experiment_subparsers.add_parser("compare")
    compare_parser.add_argument("id1")
    compare_parser.add_argument("id2")
    compare_baseline_parser = experiment_subparsers.add_parser("compare-baseline")
    compare_baseline_parser.add_argument("id")
    promote_parser = experiment_subparsers.add_parser("promote")
    promote_parser.add_argument("id")
    risk_parser = experiment_subparsers.add_parser("risk")
    risk_parser.add_argument("risk_args", nargs="+")
    feedback_parser = experiment_subparsers.add_parser("feedback")
    feedback_subparsers = feedback_parser.add_subparsers(dest="feedback_command")
    feedback_add_parser = feedback_subparsers.add_parser("add")
    feedback_add_parser.add_argument("id")
    feedback_add_parser.add_argument("--source", choices=[source.value for source in FeedbackSource], required=True)
    feedback_add_parser.add_argument("--type", required=True)
    feedback_add_parser.add_argument("--value", required=True)
    feedback_list_parser = feedback_subparsers.add_parser("list")
    feedback_list_parser.add_argument("id")
    quality_parser = experiment_subparsers.add_parser("quality")
    quality_subparsers = quality_parser.add_subparsers(dest="quality_command")
    quality_stats_parser = quality_subparsers.add_parser("stats")
    quality_stats_parser.add_argument("id")
    quality_subparsers.add_parser("rejected")
    result_parser = experiment_subparsers.add_parser("result")
    result_parser.add_argument("id")


def register_baseline_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register baseline subcommands."""

    baseline_parser = subparsers.add_parser("baseline")
    baseline_subparsers = baseline_parser.add_subparsers(dest="baseline_command")
    create_parser = baseline_subparsers.add_parser("create")
    create_parser.add_argument("--metrics", required=True)
    create_parser.add_argument("--name", default=None)
    create_parser.add_argument("--business-line-id", default=None)
    baseline_subparsers.add_parser("list")
    set_active_parser = baseline_subparsers.add_parser("set-active")
    set_active_parser.add_argument("id")


def register_risk_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register risk subcommands."""

    risk_parser = subparsers.add_parser("risk")
    risk_subparsers = risk_parser.add_subparsers(dest="risk_command")
    score_parser = risk_subparsers.add_parser("score")
    score_parser.add_argument("--type", required=True)
    score_parser.add_argument("--target", required=True)
    score_parser.add_argument("--magnitude", type=float, required=True)
    score_parser.add_argument("--blast-radius", type=float, default=None)
    score_parser.add_argument("--reversibility", type=float, required=True)
    score_parser.add_argument("--confidence", type=float, required=True)
    score_parser.add_argument("--policy-compliant", action="store_true", default=True)
    score_parser.add_argument("--policy-violated", action="store_true", default=False)
    threshold_parser = risk_subparsers.add_parser("set-threshold")
    threshold_parser.add_argument("threshold", type=float)


def register_loop_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register loop subcommands."""

    loop_parser = subparsers.add_parser("loop")
    loop_subparsers = loop_parser.add_subparsers(dest="loop_command")
    start_parser = loop_subparsers.add_parser("start")
    start_parser.add_argument("--business-line", default=None)
    start_parser.add_argument("--tick-interval", type=int, default=60)
    loop_subparsers.add_parser("stop")
    loop_subparsers.add_parser("pause")
    loop_subparsers.add_parser("resume")
    loop_subparsers.add_parser("status")
    loop_subparsers.add_parser("last-tick")
    history_parser = loop_subparsers.add_parser("history")
    history_parser.add_argument("--limit", type=int, default=10)


def handle_experiment_command(args: argparse.Namespace, db_path: str | Path) -> int:
    """Run experiment CLI commands."""

    ledger = ExperimentLedger(db_path)
    command = getattr(args, "experiment_command", None)
    if command == "run-demo":
        return _run_demo(ledger)
    if command == "list":
        return _list(ledger)
    if command == "show":
        print(ledger.generate_summary(args.id))
        return 0
    if command == "compare":
        print(json.dumps(ledger.compare(args.id1, args.id2), ensure_ascii=False, indent=2))
        return 0
    if command == "compare-baseline":
        result = ledger.compare_to_baseline(args.id)
        print(result.model_dump_json(indent=2))
        return 0
    if command == "promote":
        baseline_id = ledger.set_baseline(args.id)
        print(f"Baseline ID: {baseline_id}")
        return 0
    if command == "risk":
        return _experiment_risk(args, ledger)
    if command == "feedback":
        return _feedback(args, db_path)
    if command == "quality":
        return _quality(args, db_path)
    if command == "result":
        result = FeedbackCollector(db_path).apply_to_experiment(args.id)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    return 1


def handle_risk_command(args: argparse.Namespace, db_path: str | Path) -> int:
    """Run risk CLI commands."""

    scorer = RiskScorer(db_path)
    command = getattr(args, "risk_command", None)
    if command == "score":
        action = ActionRisk(
            action_type=args.type,
            target=args.target,
            magnitude=args.magnitude,
            blast_radius=args.blast_radius,
            reversibility=args.reversibility,
            confidence=args.confidence,
            policy_compliant=bool(args.policy_compliant and not args.policy_violated),
        )
        risk = scorer.score_action(action)
        print(risk.model_dump_json(indent=2))
        return 0
    if command == "set-threshold":
        scorer.set_threshold(args.threshold)
        print(f"Risk threshold: {scorer.get_threshold()}")
        return 0
    return 1


def handle_loop_command(args: argparse.Namespace, db_path: str | Path) -> int:
    """Run loop CLI commands."""

    engine = LoopEngine.default(db_path)
    command = getattr(args, "loop_command", None)
    if command == "start":
        tick = engine.start(business_line_id=args.business_line, tick_interval=args.tick_interval)
        print(f"Loop started, tick_interval={args.tick_interval}s, tick_id={tick.id}")
        return 0
    if command == "stop":
        engine.stop()
        print("Loop stopped")
        return 0
    if command == "pause":
        engine.pause()
        print("Loop paused")
        return 0
    if command == "resume":
        engine.resume()
        print("Loop resumed")
        return 0
    if command == "status":
        print(json.dumps(engine.get_status(), ensure_ascii=False, indent=2))
        return 0
    if command == "last-tick":
        last_tick = engine.get_last_tick()
        print("No ticks" if last_tick is None else _tick_json(last_tick))
        return 0
    if command == "history":
        ticks = engine.history(limit=args.limit)
        if not ticks:
            print("No ticks")
            return 0
        for tick in ticks:
            print(f"{tick.id}\t{tick.status.value}\t{tick.duration_ms}ms\t{tick.summary}")
        return 0
    return 1


def handle_baseline_command(args: argparse.Namespace, db_path: str | Path) -> int:
    """Run baseline CLI commands."""

    manager = BaselineManager(db_path)
    command = getattr(args, "baseline_command", None)
    if command == "create":
        metrics = _parse_metrics(args.metrics)
        baseline_id = manager.create(metrics, name=args.name, business_line_id=args.business_line_id)
        print(f"Baseline ID: {baseline_id}")
        return 0
    if command == "list":
        baselines = manager.list()
        if not baselines:
            print("No baselines")
            return 0
        for baseline in baselines:
            active = "active" if baseline.is_active else "inactive"
            print(
                f"{baseline.id}\t{active}\t{baseline.business_line_id or 'default'}\t"
                f"{baseline.name}\t{baseline.metrics}"
            )
        return 0
    if command == "set-active":
        if not manager.set_active(args.id):
            raise KeyError(f"Baseline not found: {args.id}")
        print(f"Baseline active: {args.id}")
        return 0
    return 1


def _run_demo(ledger: ExperimentLedger) -> int:
    """Create a baseline and challenger experiment."""

    baseline = Experiment(
        business_line_id="demo",
        hypothesis="建立当前策略的可比较基线。",
        action="baseline",
        before_metrics={"engagement": 10.0},
        after_metrics={"engagement": 10.0},
        result_summary="基线实验已记录，用于后续对比。",
        status=ExperimentStatus.COMPLETED,
        metadata={"demo": True, "role": "baseline"},
    )
    baseline_id = ledger.create(baseline)
    challenger = Experiment(
        business_line_id="demo",
        hypothesis="测试缩短标题长度是否提高互动率。",
        baseline_id=baseline_id,
        action="title_length=-20%",
        before_metrics={"engagement": 10.0},
        after_metrics={"engagement": 12.5},
        result_summary="互动率从10.0提升到12.5，demo challenger 优于基线。",
        status=ExperimentStatus.COMPLETED,
        metadata={"demo": True, "role": "challenger"},
    )
    challenger_id = ledger.create(challenger)
    print(ledger.generate_summary(baseline_id))
    print("")
    print(ledger.generate_summary(challenger_id))
    return 0


def _list(ledger: ExperimentLedger) -> int:
    experiments = ledger.list()
    if not experiments:
        print("No experiments")
        return 0
    for experiment in experiments:
        print(
            f"{experiment.id}\t{experiment.status.value}\t"
            f"{experiment.business_line_id or 'default'}\t{experiment.action}"
        )
    return 0


def _feedback(args: argparse.Namespace, db_path: str | Path) -> int:
    collector = FeedbackCollector(db_path)
    feedback_command = getattr(args, "feedback_command", None)
    if feedback_command == "add":
        feedback = Feedback(
            experiment_id=args.id,
            source=FeedbackSource(args.source),
            signal_type=args.type,
            value=_parse_feedback_value(args.value),
        )
        feedback_id, quality = collector.add_with_quality(feedback)
        print(f"Feedback ID: {feedback_id}")
        print(f"status={quality.status.value.upper()}, confidence={quality.confidence_score}")
        if quality.issues:
            print("issues=" + "; ".join(quality.issues))
        return 0
    if feedback_command == "list":
        feedback_items = collector.list(experiment_id=args.id)
        if not feedback_items:
            print("No feedback")
            return 0
        for feedback in feedback_items:
            print(
                f"{feedback.id}\t{feedback.source.value}\t"
                f"{feedback.signal_type}\t{feedback.value}\t{feedback.timestamp.isoformat()}"
            )
        return 0
    return 1


def _experiment_risk(args: argparse.Namespace, ledger: ExperimentLedger) -> int:
    risk_args = list(args.risk_args)
    if not risk_args:
        return 1
    if risk_args[0] == "detail":
        if len(risk_args) != 2:
            return 1
        risk = ledger.score_risk(risk_args[1])
        print(risk.model_dump_json(indent=2))
        return 0
    if len(risk_args) != 1:
        return 1
    risk = ledger.score_risk(risk_args[0])
    print(risk.model_dump_json(indent=2))
    return 0


def _quality(args: argparse.Namespace, db_path: str | Path) -> int:
    collector = FeedbackCollector(db_path)
    quality_command = getattr(args, "quality_command", None)
    if quality_command == "stats":
        print(json.dumps(collector.get_quality_stats(args.id), ensure_ascii=False, indent=2))
        return 0
    if quality_command == "rejected":
        rejected_items = collector.list_rejected_quality()
        if not rejected_items:
            print("No rejected feedback")
            return 0
        for item in rejected_items:
            print(
                f"{item['feedback_id']}\t{item['experiment_id'] or 'default'}\t"
                f"{item['source']}\t{item['signal_type']}\t{item['raw_value']}\t"
                f"confidence={item['confidence_score']}\tissues={'; '.join(item['issues'])}"
            )
        return 0
    return 1


def _parse_feedback_value(value: str) -> float | str:
    try:
        return float(value)
    except ValueError:
        return value


def _parse_metrics(metrics: str) -> dict[str, Any]:
    parsed = json.loads(metrics)
    if not isinstance(parsed, dict):
        raise ValueError("metrics must be a JSON object")
    return parsed


def _tick_json(tick: Tick) -> str:
    return tick.model_dump_json(indent=2)
