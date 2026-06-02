"""BusinessLine template tests."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from checkpoint_ai import CheckpointAI
from checkpoint_ai.templates import BusinessLineTemplate, TemplateRegistry


class TemplateTest(unittest.TestCase):
    """Validate template registration and application."""

    def test_registry_lists_builtin_templates(self) -> None:
        checkpoint_ai = CheckpointAI()

        template_ids = [template.id for template in checkpoint_ai.templates.list()]

        self.assertIn("blank", template_ids)
        self.assertIn("content", template_ids)
        self.assertIn("website", template_ids)

    def test_checkpoint_ai_creates_business_line_from_content_template(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            checkpoint_ai = CheckpointAI(sqlite_path=Path(tmp) / "checkpoint_ai.db")

            business_line = checkpoint_ai.create_business_line_from_template("我的内容业务", "content")

            self.assertEqual(business_line.name, "我的内容业务")
            self.assertIn("readability", business_line.config.evaluation_rules)
            self.assertIn("seo_quality", business_line.config.evaluation_rules)
            self.assertIn("content.writer", business_line.config.agent_templates)
            self.assertIn("publish_require_approval", business_line.config.policy_ids)

    def test_template_registry_registers_and_returns_custom_template(self) -> None:
        registry = TemplateRegistry()
        template = BusinessLineTemplate(id="custom", name="自定义业务")

        registry.register(template)

        self.assertEqual(registry.get("custom"), template)
        self.assertEqual(registry.list(), [template])


if __name__ == "__main__":
    unittest.main()
