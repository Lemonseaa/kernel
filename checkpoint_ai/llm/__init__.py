"""LLM provider exports.

LLM access remains a thin provider abstraction. Broad routing, provider proxy,
and model operation console features should be delegated to LiteLLM-style
external tooling when needed.
"""

from checkpoint_ai.llm.provider import LLMProvider, LLMRequest, LLMResponse
from checkpoint_ai.llm.providers import MiniMaxProvider, OpenAIProvider
from checkpoint_ai.llm.registry import ProviderRegistry

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
