"""Plugin registry tests."""

from __future__ import annotations

import unittest

from kernel import Kernel
from opc_os.evaluation import Evaluator
from opc_os.llm import LLMProvider, LLMRequest
from opc_os.plugins import PluginRegistry
from opc_os.runtime import BaseAgent
from opc_os.tools import BaseTool


class PluginAgent(BaseAgent):
    """Test plugin agent."""

    name = "plugin_agent"
    role = "Plugin Agent"
    capabilities = {"plugin.execute"}


class PluginTool(BaseTool):
    """Test plugin tool."""

    name = "plugin_tool"

    def run(self, **kwargs: object) -> object:
        """Return provided keyword arguments."""

        return kwargs


class PluginEvaluator(Evaluator):
    """Test plugin evaluator."""

    @property
    def name(self) -> str:
        """Return evaluator name."""

        return "plugin_evaluator"

    def evaluate(self, content: str, platform: str = "public") -> object:
        """Return a minimal fake result."""

        return {"content": content, "platform": platform}


class PluginProvider(LLMProvider):
    """Test plugin provider."""

    name = "plugin_provider"

    def _fallback_output(self, request: LLMRequest) -> str:
        """Return deterministic output."""

        return request.prompt


class PluginRegistryTest(unittest.TestCase):
    """Validate simple plugin registration."""

    def test_registry_registers_and_lists_plugin_classes(self) -> None:
        registry = PluginRegistry()

        registry.register_agent("agent", PluginAgent)
        registry.register_tool("tool", PluginTool)
        registry.register_evaluator("evaluator", PluginEvaluator)
        registry.register_provider("provider", PluginProvider)

        self.assertIs(registry.get_agent("agent"), PluginAgent)
        self.assertIs(registry.get_tool("tool"), PluginTool)
        self.assertIs(registry.get_evaluator("evaluator"), PluginEvaluator)
        self.assertIs(registry.get_provider("provider"), PluginProvider)
        self.assertEqual(registry.list_agents(), ["agent"])
        self.assertEqual(registry.list_tools(), ["tool"])
        self.assertEqual(registry.list_evaluators(), ["evaluator"])
        self.assertEqual(registry.list_providers(), ["provider"])

    def test_kernel_exposes_plugin_registry(self) -> None:
        kernel = Kernel()

        kernel.plugins.register_agent("agent", PluginAgent)

        self.assertIs(kernel.plugins.get_agent("agent"), PluginAgent)


if __name__ == "__main__":
    unittest.main()
