"""Run a lightweight long-lived kernel service process."""

from __future__ import annotations

import os
import signal
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kernel import Kernel  # noqa: E402


def main() -> int:
    """Initialize Kernel and keep the container alive for operations."""

    heartbeat_seconds = float(os.environ.get("KERNEL_SERVICE_HEARTBEAT_SECONDS", "30"))
    running = True

    def stop(_signum: int, _frame: object) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    kernel = Kernel.from_env()
    print(
        "kernel service started "
        f"db={kernel.config.sqlite_path} "
        f"provider={kernel.llm_provider.name} "
        f"model={kernel.llm_provider.model}",
        flush=True,
    )
    while running:
        report = kernel.health_checker.generate_diagnostic_report()
        print(f"kernel heartbeat status={report.overall_status}", flush=True)
        time.sleep(heartbeat_seconds)
    print("kernel service stopped", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
