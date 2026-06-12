"""Frozen legacy external Agent connection exports.

External workflow integration should move toward EvidenceAdapter connectors
and structured workflow run JSON. This package remains for compatibility with
older external-agent connection tests and API surfaces.
"""

from checkpoint_ai.external_agents.adapter import DummyExternalAgentAdapter, ExternalAgentAdapter
from checkpoint_ai.external_agents.models import ExternalAgentConnection, ExternalRunResult
from checkpoint_ai.external_agents.store import ExternalAgentConnectionStore

LEGACY_STATUS = "frozen"
REPLACEMENT_PATH = "EvidenceAdapter connector + workflow contract JSON"

__all__ = [
    "DummyExternalAgentAdapter",
    "ExternalAgentAdapter",
    "ExternalAgentConnection",
    "ExternalAgentConnectionStore",
    "ExternalRunResult",
]
