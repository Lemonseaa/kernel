"""Run a lightweight long-lived opc_os service process."""

from __future__ import annotations

import os
import signal
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from opc_os import OPCOS  # noqa: E402


def main() -> int:
    """Initialize OPC-OS and keep the container alive for operations."""

    heartbeat_seconds = float(os.environ.get("OPC_OS_SERVICE_HEARTBEAT_SECONDS", "30"))
    running = True

    def stop(_signum: int, _frame: object) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    opc_os = OPCOS.from_env()
    print(
        "opc_os service started "
        f"db={opc_os.config.sqlite_path} "
        f"provider={opc_os.llm_provider.name} "
        f"model={opc_os.llm_provider.model}",
        flush=True,
    )
    while running:
        if opc_os.ha_manager is not None:
            if not opc_os.ha_manager.heartbeat():
                opc_os.ha_manager.try_become_primary()
        report = opc_os.health_checker.generate_diagnostic_report()
        ha_status = opc_os.ha_manager.status().role if opc_os.ha_manager is not None else "disabled"
        print(f"opc_os heartbeat status={report.overall_status} ha={ha_status}", flush=True)
        time.sleep(heartbeat_seconds)
    print("opc_os service stopped", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
