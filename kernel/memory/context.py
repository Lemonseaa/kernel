"""Context manager that combines working and persistent memory."""

from __future__ import annotations

import json
from typing import Any

from kernel.memory.memory import PersistentMemory, WorkingMemory


class ContextManager:
    """Manage context across tasks in a run."""

    def __init__(self, working: WorkingMemory, persistent: PersistentMemory) -> None:
        """Create a context manager."""

        self.working = working
        self.persistent = persistent

    def add(self, run_id: str, task_id: str, content: Any) -> None:
        """Store context in both memory layers."""

        self.working.add(run_id, task_id, content)
        self.persistent.add(run_id, task_id, content)

    def get_context(self, run_id: str) -> list[dict[str, Any]]:
        """Return merged context without duplicate task ids."""

        merged: dict[str, dict[str, Any]] = {}
        for item in [*self.persistent.get_context(run_id), *self.working.get_context(run_id)]:
            merged[item["task_id"]] = item
        return list(merged.values())

    def build_prompt_context(self, run_id: str) -> str:
        """Build context text for LLM prompts."""

        items = self.get_context(run_id)
        if not items:
            return ""
        lines = ["Context:"]
        for item in items:
            content = json.dumps(item["content"], ensure_ascii=False, default=str)
            lines.append(f"- {item['task_id']}: {content}")
        return "\n".join(lines)

    def add_shared(
        self,
        business_line_id: str,
        run_id: str,
        task_id: str,
        content: Any,
        kind: str = "general",
    ) -> None:
        """Store context that should be available across runs in one BusinessLine."""

        self.persistent.add_shared(
            business_line_id=business_line_id,
            run_id=run_id,
            task_id=task_id,
            content=content,
            kind=kind,
        )

    def get_business_line_context(
        self,
        business_line_id: str,
        kind: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Return persisted context shared by runs in one BusinessLine."""

        return self.persistent.get_shared(
            business_line_id=business_line_id,
            kind=kind,
            limit=limit,
        )

    def build_business_line_prompt_context(
        self,
        business_line_id: str,
        kind: str | None = None,
        limit: int | None = 10,
    ) -> str:
        """Build cross-run BusinessLine context text for LLM prompts."""

        items = self.get_business_line_context(
            business_line_id=business_line_id,
            kind=kind,
            limit=limit,
        )
        if not items:
            return ""
        lines = ["BusinessLine Context:"]
        for item in items:
            content = json.dumps(item["content"], ensure_ascii=False, default=str)
            lines.append(f"- {item['kind']} {item['task_id']}@{item['run_id']}: {content}")
        return "\n".join(lines)
