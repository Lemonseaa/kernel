"""CLI handlers for external workflow evidence commands."""

from __future__ import annotations

import argparse
import json
from typing import Any

from checkpoint_ai.evidence.quant_drill import QuantDrillRunner
from checkpoint_ai.harness import EvidenceHarness


def register_evidence_parser(subparsers: argparse._SubParsersAction[argparse.ArgumentParser]) -> None:
    """Register evidence subcommands."""

    evidence_parser = subparsers.add_parser("evidence")
    evidence_subparsers = evidence_parser.add_subparsers(dest="evidence_command")

    ingest_parser = evidence_subparsers.add_parser("ingest")
    ingest_parser.add_argument("path")

    visualize_parser = evidence_subparsers.add_parser("visualize")
    visualize_parser.add_argument("--run", required=True, dest="run_id")

    compare_parser = evidence_subparsers.add_parser("compare")
    compare_parser.add_argument("--baseline", required=True)
    compare_parser.add_argument("--candidate", required=True)

    report_parser = evidence_subparsers.add_parser("report")
    report_parser.add_argument("--run", dest="run_id")
    report_parser.add_argument("--baseline")
    report_parser.add_argument("--candidate")

    quant_drill_parser = evidence_subparsers.add_parser("quant-drill")
    quant_drill_parser.add_argument("--candidates", type=int, default=30)
    quant_drill_parser.add_argument("--comparisons", type=int, default=5)


def handle_evidence_command(args: argparse.Namespace, db_path: str) -> int:
    """Handle evidence CLI subcommands."""

    harness = EvidenceHarness(db_path)

    if args.evidence_command == "ingest":
        result = harness.ingest_file(args.path)
        _print_json(
            {
                "run_id": result.run.run_id,
                "workflow_id": result.run.workflow_id,
                "trace_coverage": result.visualization.trace_coverage,
                "metric_coverage": result.visualization.metric_coverage,
                "black_box_node_ids": result.visualization.black_box_node_ids,
                "recommendation": result.report.recommendation.value,
                "summary": result.report.summary,
            }
        )
        return 0

    if args.evidence_command == "visualize":
        try:
            visualization = harness.visualize(args.run_id)
        except ValueError:
            print(f"Unknown run: {args.run_id}")
            return 1
        _print_json(visualization.model_dump(mode="json"))
        return 0

    if args.evidence_command == "compare":
        report = harness.compare(args.baseline, args.candidate)
        _print_json(report.model_dump(mode="json"))
        return 0

    if args.evidence_command == "report":
        if args.baseline and args.candidate:
            report = harness.compare(args.baseline, args.candidate)
            _print_json(report.model_dump(mode="json"))
            return 0
        if args.run_id:
            try:
                report = harness.report(args.run_id)
            except ValueError:
                print(f"Unknown run: {args.run_id}")
                return 1
            _print_json(report.model_dump(mode="json"))
            return 0
        print("report requires --run or --baseline and --candidate")
        return 1

    if args.evidence_command == "quant-drill":
        drill_result = QuantDrillRunner(harness.service).run(
            candidate_count=args.candidates,
            comparison_count=args.comparisons,
        )
        _print_json(
            {
                "workflow_id": drill_result.workflow_id,
                "baseline_run_id": drill_result.baseline_run_id,
                "run_count": drill_result.run_count,
                "candidate_count": drill_result.candidate_count,
                "comparison_count": len(drill_result.comparisons),
                "compared_candidate_ids": [
                    report.candidate_run_id for report in drill_result.comparisons
                ],
                "report_count": drill_result.report_count,
                "system_findings": drill_result.system_findings,
                "paper_trade_recommendation": drill_result.paper_trade_recommendation,
                "review": drill_result.review,
                "summary": drill_result.summary,
            }
        )
        return 0

    print("Unknown evidence command")
    return 1


def _print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))
