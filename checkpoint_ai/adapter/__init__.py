"""Agent adapter contracts and V2.1 demo adapter."""

from checkpoint_ai.adapter.base import AgentAdapter, AgentRunRequest, AgentRunResult
from checkpoint_ai.adapter.dummy_adapter import DummyAdapter
from checkpoint_ai.adapter.registry import AdapterRegistry

__all__ = [
    "AdapterRegistry",
    "AgentAdapter",
    "AgentRunRequest",
    "AgentRunResult",
    "DummyAdapter",
]
