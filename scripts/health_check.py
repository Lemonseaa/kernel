"""Run a lightweight OPC-OS health check."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from opc_os import OPCOS  # noqa: E402
from opc_os.models import TaskSpec  # noqa: E402


async def main() -> int:
    """Execute one in-memory workflow and print health state."""

    with TemporaryDirectory() as tmp:
        opc_os = OPCOS(sqlite_path=Path(tmp) / "opc_os.db")
        run = await opc_os.run("health", [TaskSpec(description="ping")])
        summary = opc_os.metrics.get_summary()
    if run.state.value != "succeeded":
        print(f"unhealthy: run_state={run.state.value}")
        return 1
    print(f"healthy: run_state={run.state.value} task_success={summary['task_success']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
