"""Command line interface for kernel operations."""

from __future__ import annotations

import argparse

from kernel import Kernel


def main() -> int:
    """Run the kernel CLI."""

    parser = argparse.ArgumentParser(prog="kernel")
    subparsers = parser.add_subparsers(dest="command")
    schedule_parser = subparsers.add_parser("schedule")
    schedule_subparsers = schedule_parser.add_subparsers(dest="schedule_command")
    schedule_subparsers.add_parser("list")
    args = parser.parse_args()

    if args.command == "schedule" and args.schedule_command == "list":
        kernel = Kernel()
        jobs = kernel.scheduler.list_jobs()
        if not jobs:
            print("No scheduled jobs")
            return 0
        for job in jobs:
            print(f"{job.id}\t{job.name}\t{job.job_type.value}\t{job.next_run_at}")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
