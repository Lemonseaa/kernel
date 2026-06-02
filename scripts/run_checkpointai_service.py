"""Run a lightweight long-lived checkpoint_ai service process."""

from __future__ import annotations

import os
import signal
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from checkpoint_ai import CheckpointAI  # noqa: E402


def main() -> int:
    """Initialize checkpointAI and keep the container alive for operations."""

    heartbeat_seconds = float(os.environ.get("CHECKPOINT_AI_SERVICE_HEARTBEAT_SECONDS", "30"))
    running = True

    def stop(_signum: int, _frame: object) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    checkpoint_ai = CheckpointAI.from_env()
    print(
        "checkpoint_ai service started "
        f"db={checkpoint_ai.config.sqlite_path} "
        f"provider={checkpoint_ai.llm_provider.name} "
        f"model={checkpoint_ai.llm_provider.model}",
        flush=True,
    )
    while running:
        if checkpoint_ai.ha_manager is not None:
            if not checkpoint_ai.ha_manager.heartbeat():
                checkpoint_ai.ha_manager.try_become_primary()
        report = checkpoint_ai.health_checker.generate_diagnostic_report()
        ha_status = checkpoint_ai.ha_manager.status().role if checkpoint_ai.ha_manager is not None else "disabled"
        print(f"checkpoint_ai heartbeat status={report.overall_status} ha={ha_status}", flush=True)
        time.sleep(heartbeat_seconds)
    print("checkpoint_ai service stopped", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
