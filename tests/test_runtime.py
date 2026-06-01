"""Runtime and registry tests."""

from __future__ import annotations

import unittest

from kernel.models import Agent
from kernel.runtime import AgentRegistry


class RuntimeTest(unittest.TestCase):
    """Validate agent registry behavior."""

    def test_registry_registers_and_finds_by_capability(self) -> None:
        registry = AgentRegistry()
        agent = Agent(name="writer", role="Writer", capabilities={"content.write"})

        registry.register(agent)

        self.assertEqual(registry.get(agent.id), agent)
        self.assertEqual(registry.find_by_capability("content.write"), [agent])

    def test_registry_unregisters_agent(self) -> None:
        registry = AgentRegistry()
        agent = Agent(name="writer", role="Writer", capabilities={"content.write"})
        registry.register(agent)

        registry.unregister(agent.id)

        self.assertIsNone(registry.get(agent.id))
