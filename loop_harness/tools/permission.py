"""Tool permission checks."""

from __future__ import annotations


class ToolPermission:
    """Allowlist-based tool permission checker."""

    def __init__(
        self,
        allowed_tools: set[str] | None = None,
        risk_levels: dict[str, str] | None = None,
        allow_high_risk: bool = False,
    ) -> None:
        """Create a permission checker."""

        self.allowed_tools = allowed_tools or set()
        self.risk_levels = risk_levels or {}
        self.allow_high_risk = allow_high_risk

    def check(self, tool_name: str) -> bool:
        """Return whether a tool can be called."""

        return tool_name in self.allowed_tools and not self.requires_approval(tool_name)

    def requires_approval(self, tool_name: str) -> bool:
        """Return whether a tool should be blocked for approval."""

        return self.risk_levels.get(tool_name) == "high" and not self.allow_high_risk
