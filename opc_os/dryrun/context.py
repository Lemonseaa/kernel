"""Dry run context manager."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from opc_os.opc_os import OPCOS


class DryRunContext:
    """Temporarily enable dry run mode for a opc_os."""

    def __init__(self, opc_os: "OPCOS") -> None:
        """Create a context manager for a opc_os."""

        self.opc_os = opc_os
        self.previous_opc_os_state = False
        self.previous_tool_state = False

    def __enter__(self) -> "OPCOS":
        """Enable dry run mode."""

        self.previous_opc_os_state = self.opc_os.dry_run_enabled
        self.previous_tool_state = self.opc_os.tool_registry.dry_run
        self.opc_os.set_dry_run(True)
        return self.opc_os

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        """Restore the previous mode."""

        self.opc_os.set_dry_run(self.previous_opc_os_state)
        self.opc_os.tool_registry.dry_run = self.previous_tool_state
