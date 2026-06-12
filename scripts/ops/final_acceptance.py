"""Run the V1.0 final acceptance suite."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

COMMANDS = [
    [sys.executable, "-m", "ruff", "check", "loop_harness", "tests", "scripts"],
    [sys.executable, "-m", "mypy", "loop_harness", "--show-error-codes", "--no-incremental"],
    [sys.executable, "-m", "compileall", "-q", "loop_harness", "tests", "scripts"],
    [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
    [sys.executable, "scripts/ops/benchmark.py", "--runs", "20"],
    [sys.executable, "scripts/ops/stress_test.py", "--runs", "50", "--concurrency", "5"],
    [sys.executable, "scripts/ops/security_audit.py"],
]


def main() -> int:
    """Run all acceptance commands and stop on the first failure."""

    root = _project_root()
    for command in COMMANDS:
        print(f"acceptance_run command={' '.join(command)}", flush=True)
        result = subprocess.run(command, cwd=root, check=False)
        if result.returncode != 0:
            print(f"acceptance_failed command={' '.join(command)} returncode={result.returncode}")
            return result.returncode
    print("acceptance_summary status=passed")
    return 0


def _project_root() -> Path:
    """Return the repository root from this nested script location."""

    current = Path(__file__).resolve()
    for parent in current.parents:
        if (parent / "pyproject.toml").exists() and (parent / "loop_harness").is_dir():
            return parent
    raise RuntimeError("Could not locate Loop Harness project root")


if __name__ == "__main__":
    raise SystemExit(main())
