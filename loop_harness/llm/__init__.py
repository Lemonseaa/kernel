"""LLM provider exports.

LLM access remains a thin provider abstraction. Broad routing, provider proxy,
and model operation console features should be delegated to LiteLLM-style
external tooling when needed.
"""

from loop_harness.llm.provider import LLMProvider, LLMRequest, LLMResponse
from loop_harness.llm.providers import MiniMaxProvider, OpenAIProvider
from loop_harness.llm.registry import ProviderRegistry

CLEANUP_STATUS = "isolate"
REPLACEMENT_PATH = "thin adapter; LiteLLM-compatible layer for breadth"

__all__ = [
    "LLMProvider",
    "LLMRequest",
    "LLMResponse",
    "MiniMaxProvider",
    "OpenAIProvider",
    "ProviderRegistry",
]
