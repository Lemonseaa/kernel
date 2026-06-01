"""Shell tool."""

from __future__ import annotations

import subprocess
from typing import Any

from kernel.tools.base import BaseTool


class ShellTool(BaseTool):
    """Run allowlisted shell commands."""

    name = "shell"
    description = "Run an allowlisted shell command."

    def __init__(self, allowed_commands: set[str] | None = None, timeout: int = 30) -> None:
        """Create a shell tool with command allowlist."""

        self.allowed_commands = allowed_commands or set()
        self.timeout = timeout

    def run(self, **kwargs: Any) -> dict[str, object]:
        """Run a command if it is allowlisted."""

        command = kwargs.get("command")
        if not isinstance(command, list) or not command:
            raise ValueError("ShellTool requires command as a non-empty list.")
        if command[0] not in self.allowed_commands:
            raise PermissionError(f"Shell command is not allowed: {command[0]}")
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=self.timeout,
        )
        return {
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        }
