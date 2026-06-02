"""CLI commands for Experiment Ledger."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from checkpoint_ai.experiment.feedback import Feedback, FeedbackCollector, FeedbackSource
from checkpoint_ai.experiment.ledger import ExperimentLedger
from checkpoint_ai.experiment.models import Experiment, ExperimentStatus


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
    if command == "feedback":
        return _feedback(args, db_path)
    if command == "quality":
        return _quality(args, db_path)
    if command == "result":
        result = FeedbackCollector(db_path).apply_to_experiment(args.id)
        print(json.dumps(result, ensure_ascii=False, indent=2))
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
