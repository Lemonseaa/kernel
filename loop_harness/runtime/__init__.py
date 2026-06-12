"""Frozen legacy Agent runtime exports.

LoopHarness no longer builds a generic Agent runtime. These exports remain
for compatibility with the historical Kernel tests and old workflow engine.
New mainline work should connect external workflows through evidence adapters
instead of spawning internal agents here.
"""

from loop_harness.runtime.base import BaseAgent, LLMAgent, SimpleAgent
from loop_harness.runtime.registry import AgentRegistry

LEGACY_STATUS = "frozen"
REPLACEMENT_PATH = "external agent runtimes / workflow-specific harnesses"

__all__ = ["AgentRegistry", "BaseAgent", "LLMAgent", "SimpleAgent"]
