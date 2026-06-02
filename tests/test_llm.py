"""LLM provider abstraction tests."""

from __future__ import annotations

import unittest

from opc_os.config import KernelConfig
from kernel import Kernel
from opc_os.llm import LLMRequest, MiniMaxProvider, OpenAIProvider, ProviderRegistry
from opc_os.models import Task
from opc_os.runtime import LLMAgent


class LLMProviderTest(unittest.TestCase):
    """Validate provider registration, configuration, and LLM agent execution."""

    def test_provider_registry_registers_and_resolves_default_provider(self) -> None:
        registry = ProviderRegistry()
        provider = MiniMaxProvider(api_key="test-key", transport=lambda request: "minimax ok")

        registry.register(provider, default=True)

        self.assertIs(registry.get("minimax"), provider)
        self.assertIs(registry.default(), provider)

    def test_openai_provider_uses_injected_transport(self) -> None:
        provider = OpenAIProvider(api_key="test-key", transport=lambda request: request.prompt.upper())

        response = provider.generate(LLMRequest(prompt="hello"))

        self.assertEqual(response.output, "HELLO")
        self.assertEqual(response.provider, "openai")

    def test_llm_agent_returns_provider_output_artifact(self) -> None:
        provider = MiniMaxProvider(api_key="test-key", transport=lambda request: "draft content")
        agent = LLMAgent(provider=provider)
        task = Task(name="write", agent_capability="llm.generate", input="write a post")

        artifact = agent.execute(task)

        self.assertEqual(artifact.content["output"], "draft content")
        self.assertEqual(artifact.content["agent"], "llm")
        self.assertEqual(artifact.content["provider"], "minimax")

    def test_kernel_config_builds_default_provider(self) -> None:
        config = KernelConfig(
            providers={"minimax": {"api_key": "test-key", "model": "MiniMax-M2.7-highspeed"}},
            default_provider="minimax",
        )

        provider = config.llm_provider

        self.assertEqual(provider.name, "minimax")
        self.assertEqual(provider.model, "MiniMax-M2.7-highspeed")

    def test_kernel_accepts_configured_default_provider(self) -> None:
        config = KernelConfig(
            providers={"openai": {"api_key": "test-key", "model": "gpt-test"}},
            default_provider="openai",
        )

        kernel = Kernel(config=config)

        self.assertEqual(kernel.llm_provider.name, "openai")
        self.assertEqual(kernel.provider_registry.default().model, "gpt-test")
