"""Transitional Agent adapter contracts.

This package is still used by V2-V7 demos, shadow runs, and compatibility
tests. Future mainline adapters should be shaped as EvidenceAdapter connectors
that export workflow run JSON rather than deep agent-platform integrations.
"""

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

LEGACY_STATUS = "rewrite"
REPLACEMENT_PATH = "checkpoint_ai.evidence EvidenceAdapter connectors"

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
