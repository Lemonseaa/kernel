"""Command line interface for checkpointAI operations."""
from __future__ import annotations

import argparse
import asyncio
import json
from typing import cast

from checkpoint_ai import CheckpointAI
from checkpoint_ai.config import CheckpointAIConfig
from checkpoint_ai.dryrun import DryRunValidator
from checkpoint_ai.experiment.cli import (
    handle_baseline_command,
    handle_experiment_command,
    handle_loop_command,
    handle_risk_command,
    register_baseline_parser,
    register_experiment_parser,
    register_loop_parser,
    register_risk_parser,
)
from checkpoint_ai.models import Run, TaskSpec
from checkpoint_ai.notification import ConsoleNotificationChannel, NotificationMessage


def main(argv: list[str] | None = None) -> int:
    """Run the checkpoint_ai CLI."""

    parser = argparse.ArgumentParser(prog="checkpointai")
    parser.add_argument("--db", default=None)
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("status")
    health_parser = subparsers.add_parser("health")
    health_parser.add_argument("--json", action="store_true", default=True)
    run_parser = subparsers.add_parser("run")
    run_subparsers = run_parser.add_subparsers(dest="run_command")
    run_subparsers.add_parser("list")
    bl_parser = subparsers.add_parser("bl")
    bl_subparsers = bl_parser.add_subparsers(dest="bl_command")
    bl_subparsers.add_parser("list")
    schedule_parser = subparsers.add_parser("schedule")
    schedule_subparsers = schedule_parser.add_subparsers(dest="schedule_command")
    schedule_subparsers.add_parser("list")
    notify_parser = subparsers.add_parser("notify")
    notify_parser.add_argument("--title", required=True)
    notify_parser.add_argument("--body", required=True)
    notify_parser.add_argument("--type", default="info")
    notify_parser.add_argument("--priority", default="normal")
    dryrun_parser = subparsers.add_parser("dryrun")
    dryrun_parser.add_argument("--task", required=True)
    register_experiment_parser(subparsers)
    register_baseline_parser(subparsers)
    register_risk_parser(subparsers)
    register_loop_parser(subparsers)
    args = parser.parse_args(argv)

    if args.command == "status":
        checkpoint_ai = CheckpointAI.from_env() if args.db is None else CheckpointAI(sqlite_path=args.db)
        status = {
            "runs": len(checkpoint_ai.store.list_runs()),
            "business_lines": len(checkpoint_ai.business_lines.list()),
            "events": len(checkpoint_ai.event_bus.events),
            "alerts": len(checkpoint_ai.alert_manager.alerts),
            "health": checkpoint_ai.health_checker.generate_diagnostic_report().overall_status,
        }
        print(json.dumps(status, ensure_ascii=False))
        return 0

    if args.command == "run" and args.run_command == "list":
        checkpoint_ai = CheckpointAI.from_env() if args.db is None else CheckpointAI(sqlite_path=args.db)
        runs = checkpoint_ai.store.list_runs()
        if not runs:
            print("No runs")
            return 0
        for run_row in runs:
            print(
                f"{run_row['id']}\t{run_row['state']}\t"
                f"{run_row['business_line_id']}\t{run_row['user_request']}"
            )
        return 0

    if args.command == "bl" and args.bl_command == "list":
        checkpoint_ai = CheckpointAI.from_env() if args.db is None else CheckpointAI(sqlite_path=args.db)
        business_lines = checkpoint_ai.business_lines.list()
        if not business_lines:
            print("No business lines")
            return 0
        for business_line in business_lines:
            print(f"{business_line.id}\t{business_line.status.value}\t{business_line.name}")
        return 0

    if args.command == "health":
        checkpoint_ai = CheckpointAI.from_env() if args.db is None else CheckpointAI(sqlite_path=args.db)
        print(json.dumps(checkpoint_ai.health_checker.generate_diagnostic_report().to_dict(), ensure_ascii=False))
        return 0

    if args.command == "schedule" and args.schedule_command == "list":
        checkpoint_ai = CheckpointAI.from_env() if args.db is None else CheckpointAI(sqlite_path=args.db)
        jobs = checkpoint_ai.scheduler.list_jobs()
        if not jobs:
            print("No scheduled jobs")
            return 0
        for job in jobs:
            print(f"{job.id}\t{job.name}\t{job.job_type.value}\t{job.next_run_at}")
        return 0

    if args.command == "notify":
        checkpoint_ai = CheckpointAI.from_env() if args.db is None else CheckpointAI(sqlite_path=args.db)
        checkpoint_ai.notification_manager.register(ConsoleNotificationChannel())
        checkpoint_ai.notification_manager.notify(
            NotificationMessage(
                title=args.title,
                body=args.body,
                type=args.type,
                priority=args.priority,
            )
        )
        return 0

    if args.command == "dryrun":
        spec = TaskSpec(description=args.task)
        validation = DryRunValidator().validate_task_specs([spec])
        if not validation.valid:
            print(json.dumps({"dry_run": True, "valid": False, "errors": validation.errors}, ensure_ascii=False))
            return 1
        checkpoint_ai = CheckpointAI(sqlite_path=args.db, config=CheckpointAIConfig(dry_run=True))
        dryrun_result = cast(Run, asyncio.run(checkpoint_ai.run("dryrun preview", [spec])))
        print(
            json.dumps(
                {
                    "dry_run": True,
                    "run_id": dryrun_result.id,
                    "state": dryrun_result.state.value,
                    "tasks": [
                        {"id": task.id, "state": task.state.value, "result": task.result}
                        for task in dryrun_result.tasks
                    ],
                    "warnings": validation.warnings,
                },
                ensure_ascii=False,
            )
        )
        return 0

    if args.command == "experiment":
        db_path = args.db or CheckpointAIConfig.from_env().sqlite_path
        return handle_experiment_command(args, db_path)

    if args.command == "baseline":
        db_path = args.db or CheckpointAIConfig.from_env().sqlite_path
        return handle_baseline_command(args, db_path)

    if args.command == "risk":
        db_path = args.db or CheckpointAIConfig.from_env().sqlite_path
        return handle_risk_command(args, db_path)

    if args.command == "loop":
        db_path = args.db or CheckpointAIConfig.from_env().sqlite_path
        return handle_loop_command(args, db_path)

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
