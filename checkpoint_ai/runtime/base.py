"""Base agent runtime abstraction."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable

from checkpoint_ai.llm import LLMProvider, LLMRequest
from checkpoint_ai.memory import ContextManager
from checkpoint_ai.models import Agent, Artifact, Task


class BaseAgent(ABC):
    """Abstract base class for executable agents."""

    name: str = "base"
    role: str = "Base Agent"
    capabilities: set[str] = set()

    def to_model(self) -> Agent:
        """Return registry metadata for this agent."""

        return Agent(name=self.name, role=self.role, capabilities=set(self.capabilities))

    @abstractmethod
    def execute(self, task: Task) -> Artifact:
        """Execute a task and return an artifact."""


class SimpleAgent(BaseAgent):
    """Default executable agent for simple task specs."""

    name = "simple"
    role = "Simple Agent"
    capabilities = {"simple.execute"}

    def execute(self, task: Task) -> Artifact:
        """Echo task input or description as a text artifact."""

        content = task.input if task.input is not None else task.name
        return Artifact(task_id=task.id, run_id=task.run_id or "", kind="text", content=content)


class LLMAgent(BaseAgent):
    """Agent that delegates generation to an LLM provider."""

    name = "llm"
    role = "LLM Agent"
    capabilities = {"llm.generate"}

    def __init__(
        self,
        provider: LLMProvider,
        memory: ContextManager | None = None,
        transport: Callable[[LLMRequest], str] | None = None,
    ) -> None:
        """Create an LLM-backed agent."""

        self.provider = provider
        self.memory = memory
        if transport is not None:
            self.provider.transport = transport

    def execute(self, task: Task) -> Artifact:
        """Generate content for a task."""

        prompt = str(task.input if task.input is not None else task.name)
        if self.memory is not None and task.run_id:
            contexts = []
            run_context = self.memory.build_prompt_context(task.run_id)
            if run_context:
                contexts.append(run_context)
            business_line_context = self.memory.build_business_line_prompt_context(
                task.business_line_id,
                kind="evaluation_feedback",
            )
            if business_line_context:
                contexts.append(business_line_context)
            if contexts:
                context_text = "\n\n".join(contexts)
                prompt = f"{context_text}\n\nTask:\n{prompt}"
        response = self.provider.generate(LLMRequest(prompt=prompt, metadata={"task_id": task.id}))
        return Artifact(
            task_id=task.id,
            run_id=task.run_id or "",
            kind="llm_response",
            content={
                "output": response.output,
                "provider": response.provider,
                "model": response.model,
                "agent": self.name,
            },
        )
