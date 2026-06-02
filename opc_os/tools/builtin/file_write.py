"""File write tool."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from opc_os.tools.base import BaseTool


class FileWriteTool(BaseTool):
    """Write text files below a configured root directory."""

    name = "file_write"
    description = "Write a text file below the configured root directory."

    def __init__(self, root_dir: str | Path = ".") -> None:
        """Create a file writer constrained to root_dir."""

        self.root_dir = Path(root_dir).resolve()

    def run(self, **kwargs: Any) -> dict[str, str]:
        """Write content to a relative path."""

        raw_path = kwargs.get("path")
        if not raw_path:
            raise ValueError("FileWriteTool requires path.")
        content = str(kwargs.get("content", ""))
        target = (self.root_dir / str(raw_path)).resolve()
        if self.root_dir not in target.parents and target != self.root_dir:
            raise PermissionError("FileWriteTool path escapes root_dir.")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return {"path": str(target), "status": "written"}
