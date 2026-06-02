"""Run a lightweight Kernel health check."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kernel import Kernel  # noqa: E402
from kernel.models import TaskSpec  # noqa: E402


async def main() -> int:
    """Execute one in-memory workflow and print health state."""

    with TemporaryDirectory() as tmp:
        kernel = Kernel(sqlite_path=Path(tmp) / "kernel.db")
        run = await kernel.run("health", [TaskSpec(description="ping")])
        summary = kernel.metrics.get_summary()
    if run.state.value != "succeeded":
        print(f"unhealthy: run_state={run.state.value}")
        return 1
    print(f"healthy: run_state={run.state.value} task_success={summary['task_success']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
