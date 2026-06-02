"""Run a lightweight OPC-OS stress test."""

from __future__ import annotations

import argparse
import asyncio
import sys
import time
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from opc_os import OPCOS  # noqa: E402
from opc_os.models import TaskSpec  # noqa: E402


async def _run_workflow(opc_os: OPCOS, index: int) -> str:
    """Run one workflow and return state."""

    run = await opc_os.run(f"stress-{index}", [TaskSpec(description=f"task-{index}")])
    return run.state.value


async def _main(runs: int, concurrency: int) -> int:
    """Execute concurrent workflow runs."""

    with TemporaryDirectory() as tmp:
        opc_os = OPCOS(sqlite_path=Path(tmp) / "opc_os.db")
        started_at = time.perf_counter()
        states: list[str] = []
        for offset in range(0, runs, concurrency):
            batch = range(offset, min(offset + concurrency, runs))
            states.extend(await asyncio.gather(*[_run_workflow(opc_os, index) for index in batch]))
        elapsed = time.perf_counter() - started_at
    failures = sum(1 for state in states if state != "succeeded")
    print(
        "stress_summary "
        f"runs={runs} concurrency={concurrency} failures={failures} elapsed_seconds={elapsed:.6f}",
        flush=True,
    )
    return 0 if failures == 0 else 1


def main(argv: list[str] | None = None) -> int:
    """Parse CLI args and run stress test."""

    parser = argparse.ArgumentParser()
    parser.add_argument("--runs", type=int, default=50)
    parser.add_argument("--concurrency", type=int, default=5)
    args = parser.parse_args(argv)
    if args.runs <= 0 or args.concurrency <= 0:
        raise ValueError("--runs and --concurrency must be greater than zero")
    return asyncio.run(_main(args.runs, args.concurrency))


if __name__ == "__main__":
    raise SystemExit(main())
