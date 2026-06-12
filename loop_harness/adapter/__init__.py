"""Transitional Agent adapter contracts.

This package is still used by V2-V7 demos, shadow runs, and compatibility
tests. Future mainline adapters should be shaped as EvidenceAdapter connectors
that export workflow run JSON rather than deep agent-platform integrations.
"""

from loop_harness.adapter.base import AgentAdapter, AgentRunRequest, AgentRunResult
from loop_harness.adapter.capabilities import (
    AdapterCapabilities,
    AdapterDescription,
    CapabilitySupport,
)
from loop_harness.adapter.compatibility import (
    AdapterCompatibilityDecision,
    AdapterCompatibilityEvaluator,
    AdapterCompatibilityInput,
    AdapterCompatibilityReport,
    AdapterCompatibilityReportStore,
)
from loop_harness.adapter.dummy_adapter import DummyAdapter
from loop_harness.adapter.opc_agent_adapter import OPCAgentAdapter
from loop_harness.adapter.quant_research_adapter import QuantResearchDemoAdapter
from loop_harness.adapter.registry import AdapterRegistry

LEGACY_STATUS = "rewrite"
REPLACEMENT_PATH = "loop_harness.evidence EvidenceAdapter connectors"

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
