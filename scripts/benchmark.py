"""Run a lightweight checkpointAI performance benchmark."""

from __future__ import annotations

import argparse
import asyncio
import statistics
import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from checkpoint_ai import CheckpointAI  # noqa: E402
from checkpoint_ai.models import TaskSpec  # noqa: E402


async def _run_once() -> float:
    """Run one small workflow and return duration."""

    with TemporaryDirectory() as tmp:
        checkpoint_ai = CheckpointAI(sqlite_path=Path(tmp) / "checkpoint_ai.db")
        started_at = time.perf_counter()
        run = await checkpoint_ai.run("benchmark", [TaskSpec(description="ping")])
        duration = time.perf_counter() - started_at
    if run.state.value != "succeeded":
        raise RuntimeError(f"benchmark run failed: {run.state.value}")
    return duration


async def _main(runs: int) -> int:
    """Run benchmark iterations."""

    durations = [await _run_once() for _ in range(runs)]
    print(
        "benchmark_summary "
        f"runs={runs} "
        f"avg_seconds={statistics.mean(durations):.6f} "
        f"max_seconds={max(durations):.6f}",
        flush=True,
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    """Parse CLI args and run benchmark."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=20)
    args = parser.parse_args(argv)
    if args.runs <= 0:
        raise ValueError("--runs must be greater than zero")
    return asyncio.run(_main(args.runs))


if __name__ == "__main__":
    raise SystemExit(main())
