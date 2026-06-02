"""Run the V1.0 final acceptance suite."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

COMMANDS = [
    [sys.executable, "-m", "ruff", "check", "opc_os", "tests", "scripts"],
    [sys.executable, "-m", "mypy", "opc_os", "--show-error-codes", "--no-incremental"],
    [sys.executable, "-m", "compileall", "-q", "opc_os", "tests", "scripts"],
    [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
    [sys.executable, "scripts/benchmark.py", "--runs", "20"],
    [sys.executable, "scripts/stress_test.py", "--runs", "50", "--concurrency", "5"],
    [sys.executable, "scripts/security_audit.py"],
]


def main() -> int:
    """Run all acceptance commands and stop on the first failure."""

    root = Path(__file__).resolve().parents[1]
    for command in COMMANDS:
        print(f"acceptance_run command={' '.join(command)}", flush=True)
        result = subprocess.run(command, cwd=root, check=False)
        if result.returncode != 0:
            print(f"acceptance_failed command={' '.join(command)} returncode={result.returncode}")
            return result.returncode
    print("acceptance_summary status=passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
