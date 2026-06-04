"""Structured adapter capability contracts."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class CapabilitySupport(str, Enum):
    """Capability support level."""

    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    PARTIAL = "partial"


class AdapterCapabilities(BaseModel):
    """Structured capability declaration for one adapter."""

    prompt_injection: CapabilitySupport = CapabilitySupport.UNSUPPORTED
    metrics_capture: CapabilitySupport = CapabilitySupport.UNSUPPORTED
    shadow_run: CapabilitySupport = CapabilitySupport.UNSUPPORTED
    run_trace: CapabilitySupport = CapabilitySupport.UNSUPPORTED
    continuous_params: CapabilitySupport = CapabilitySupport.UNSUPPORTED
    structured_input: CapabilitySupport = CapabilitySupport.SUPPORTED
    structured_output: CapabilitySupport = CapabilitySupport.SUPPORTED
    notes: dict[str, str] = Field(default_factory=dict)

    def supports(self, capability: str) -> bool:
        """Return true when capability is fully supported."""

        value = getattr(self, capability)
        if not isinstance(value, CapabilitySupport):
            raise AttributeError(f"Unknown adapter capability: {capability}")
        return value == CapabilitySupport.SUPPORTED


class AdapterDescription(BaseModel):
    """Registry-facing adapter description."""

    name: str
    supported_task_types: list[str]
    capabilities: AdapterCapabilities
