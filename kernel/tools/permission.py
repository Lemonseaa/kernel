"""Tool permission checks."""

from __future__ import annotations


class ToolPermission:
    """Allowlist-based tool permission checker."""

    def __init__(self, allowed_tools: set[str] | None = None) -> None:
        """Create a permission checker."""

        self.allowed_tools = allowed_tools or set()

    def check(self, tool_name: str) -> bool:
        """Return whether a tool can be called."""

        return tool_name in self.allowed_tools
