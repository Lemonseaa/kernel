"""Command line interface for OPC-OS operations."""
from __future__ import annotations

import argparse
import asyncio
import json
from typing import cast

from opc_os import OPCOS
from opc_os.config import OPCOSConfig
from opc_os.dryrun import DryRunValidator
from opc_os.models import Run, TaskSpec
from opc_os.notification import ConsoleNotificationChannel, NotificationMessage


def main(argv: list[str] | None = None) -> int:
    """Run the opc_os CLI."""

    parser = argparse.ArgumentParser(prog="opc-os")
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
    args = parser.parse_args(argv)

    if args.command == "status":
        opc_os = OPCOS.from_env() if args.db is None else OPCOS(sqlite_path=args.db)
        status = {
            "runs": len(opc_os.store.list_runs()),
            "business_lines": len(opc_os.business_lines.list()),
            "events": len(opc_os.event_bus.events),
            "alerts": len(opc_os.alert_manager.alerts),
            "health": opc_os.health_checker.generate_diagnostic_report().overall_status,
        }
        print(json.dumps(status, ensure_ascii=False))
        return 0

    if args.command == "run" and args.run_command == "list":
        opc_os = OPCOS.from_env() if args.db is None else OPCOS(sqlite_path=args.db)
        runs = opc_os.store.list_runs()
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
        opc_os = OPCOS.from_env() if args.db is None else OPCOS(sqlite_path=args.db)
        business_lines = opc_os.business_lines.list()
        if not business_lines:
            print("No business lines")
            return 0
        for business_line in business_lines:
            print(f"{business_line.id}\t{business_line.status.value}\t{business_line.name}")
        return 0

    if args.command == "health":
        opc_os = OPCOS.from_env() if args.db is None else OPCOS(sqlite_path=args.db)
        print(json.dumps(opc_os.health_checker.generate_diagnostic_report().to_dict(), ensure_ascii=False))
        return 0

    if args.command == "schedule" and args.schedule_command == "list":
        opc_os = OPCOS.from_env() if args.db is None else OPCOS(sqlite_path=args.db)
        jobs = opc_os.scheduler.list_jobs()
        if not jobs:
            print("No scheduled jobs")
            return 0
        for job in jobs:
            print(f"{job.id}\t{job.name}\t{job.job_type.value}\t{job.next_run_at}")
        return 0

    if args.command == "notify":
        opc_os = OPCOS.from_env() if args.db is None else OPCOS(sqlite_path=args.db)
        opc_os.notification_manager.register(ConsoleNotificationChannel())
        opc_os.notification_manager.notify(
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
        opc_os = OPCOS(sqlite_path=args.db, config=OPCOSConfig(dry_run=True))
        dryrun_result = cast(Run, asyncio.run(opc_os.run("dryrun preview", [spec])))
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

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
