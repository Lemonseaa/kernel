"""Run a lightweight checkpointAI health check."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from checkpoint_ai import CheckpointAI  # noqa: E402
from checkpoint_ai.models import TaskSpec  # noqa: E402


async def main() -> int:
    """Execute one in-memory workflow and print health state."""

    with TemporaryDirectory() as tmp:
        checkpoint_ai = CheckpointAI(sqlite_path=Path(tmp) / "checkpoint_ai.db")
        run = await checkpoint_ai.run("health", [TaskSpec(description="ping")])
        summary = checkpoint_ai.metrics.get_summary()
    if run.state.value != "succeeded":
        print(f"unhealthy: run_state={run.state.value}")
        return 1
    print(f"healthy: run_state={run.state.value} task_success={summary['task_success']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
