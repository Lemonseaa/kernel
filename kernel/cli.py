"""Command line interface for kernel operations."""

from __future__ import annotations

import argparse
import asyncio
import json

from kernel import Kernel
from kernel.config import KernelConfig
from kernel.dryrun import DryRunValidator
from kernel.models import TaskSpec
from kernel.notification import ConsoleNotificationChannel, NotificationMessage


def main(argv: list[str] | None = None) -> int:
    """Run the kernel CLI."""

    parser = argparse.ArgumentParser(prog="kernel")
    subparsers = parser.add_subparsers(dest="command")
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

    if args.command == "schedule" and args.schedule_command == "list":
        kernel = Kernel()
        jobs = kernel.scheduler.list_jobs()
        if not jobs:
            print("No scheduled jobs")
            return 0
        for job in jobs:
            print(f"{job.id}\t{job.name}\t{job.job_type.value}\t{job.next_run_at}")
        return 0

    if args.command == "notify":
        kernel = Kernel()
        kernel.notification_manager.register(ConsoleNotificationChannel())
        kernel.notification_manager.notify(
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
        kernel = Kernel(config=KernelConfig(dry_run=True))
        run = asyncio.run(kernel.run("dryrun preview", [spec]))
        print(
            json.dumps(
                {
                    "dry_run": True,
                    "run_id": run.id,
                    "state": run.state.value,
                    "tasks": [{"id": task.id, "state": task.state.value, "result": task.result} for task in run.tasks],
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
