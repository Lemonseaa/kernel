"""Frozen legacy Agent runtime exports.

CheckpointAI no longer builds a generic Agent runtime. These exports remain
for compatibility with the historical Kernel tests and old workflow engine.
New mainline work should connect external workflows through evidence adapters
instead of spawning internal agents here.
"""

from checkpoint_ai.runtime.base import BaseAgent, LLMAgent, SimpleAgent
from checkpoint_ai.runtime.registry import AgentRegistry

LEGACY_STATUS = "frozen"
REPLACEMENT_PATH = "external agent runtimes / workflow-specific harnesses"

__all__ = ["AgentRegistry", "BaseAgent", "LLMAgent", "SimpleAgent"]
