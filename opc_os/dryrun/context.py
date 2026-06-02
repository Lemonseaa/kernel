"""Dry run context manager."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from opc_os.kernel import Kernel


class DryRunContext:
    """Temporarily enable dry run mode for a kernel."""

    def __init__(self, kernel: "Kernel") -> None:
        """Create a context manager for a kernel."""

        self.kernel = kernel
        self.previous_kernel_state = False
        self.previous_tool_state = False

    def __enter__(self) -> "Kernel":
        """Enable dry run mode."""

        self.previous_kernel_state = self.kernel.dry_run_enabled
        self.previous_tool_state = self.kernel.tool_registry.dry_run
        self.kernel.set_dry_run(True)
        return self.kernel

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        """Restore the previous mode."""

        self.kernel.set_dry_run(self.previous_kernel_state)
        self.kernel.tool_registry.dry_run = self.previous_tool_state
