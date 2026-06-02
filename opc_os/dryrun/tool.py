"""Dry run tool simulation."""

from __future__ import annotations

from typing import Any

from opc_os.tools.base import BaseTool


class DryRunTool(BaseTool):
    """Tool simulator that records intent without side effects."""

    description = "Simulate a tool call without executing it."

    def __init__(self, tool_name: str) -> None:
        """Create a simulator for a named tool."""

        self.name = tool_name

    def run(self, **kwargs: Any) -> dict[str, Any]:
        """Return a dry run result for a tool call."""

        return {
            "dry_run": True,
            "tool": self.name,
            "arguments": kwargs,
            "output": f"[DRY RUN] Tool {self.name} would be executed.",
        }
