"""Run a lightweight long-lived loop_harness service process."""

from __future__ import annotations

import os
import signal
import sys
import time
from pathlib import Path

ROOT = next(
    parent
    for parent in Path(__file__).resolve().parents
    if (parent / "pyproject.toml").exists() and (parent / "loop_harness").is_dir()
)
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from loop_harness import LoopHarness  # noqa: E402


def main() -> int:
    """Initialize Loop Harness and keep the container alive for operations."""

    heartbeat_seconds = float(os.environ.get("LOOP_HARNESS_SERVICE_HEARTBEAT_SECONDS", "30"))
    running = True

    def stop(_signum: int, _frame: object) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    loop_harness = LoopHarness.from_env()
    print(
        "loop_harness service started "
        f"db={loop_harness.config.sqlite_path} "
        f"provider={loop_harness.llm_provider.name} "
        f"model={loop_harness.llm_provider.model}",
        flush=True,
    )
    while running:
        report = loop_harness.health_checker.generate_diagnostic_report()
        ha_status = "externalized"
        print(f"loop_harness heartbeat status={report.overall_status} ha={ha_status}", flush=True)
        time.sleep(heartbeat_seconds)
    print("loop_harness service stopped", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
