"""Agent adapter contracts and V2.1 demo adapter."""

from checkpoint_ai.adapter.base import AgentAdapter, AgentRunRequest, AgentRunResult
from checkpoint_ai.adapter.capabilities import (
    AdapterCapabilities,
    AdapterDescription,
    CapabilitySupport,
)
from checkpoint_ai.adapter.compatibility import (
    AdapterCompatibilityDecision,
    AdapterCompatibilityEvaluator,
    AdapterCompatibilityInput,
    AdapterCompatibilityReport,
    AdapterCompatibilityReportStore,
)
from checkpoint_ai.adapter.dummy_adapter import DummyAdapter
from checkpoint_ai.adapter.opc_agent_adapter import OPCAgentAdapter
from checkpoint_ai.adapter.quant_research_adapter import QuantResearchDemoAdapter
from checkpoint_ai.adapter.registry import AdapterRegistry

__all__ = [
    "AdapterRegistry",
    "AdapterCapabilities",
    "AdapterCompatibilityDecision",
    "AdapterCompatibilityEvaluator",
    "AdapterCompatibilityInput",
    "AdapterCompatibilityReport",
    "AdapterCompatibilityReportStore",
    "AdapterDescription",
    "AgentAdapter",
    "AgentRunRequest",
    "AgentRunResult",
    "CapabilitySupport",
    "DummyAdapter",
    "OPCAgentAdapter",
    "QuantResearchDemoAdapter",
]
