"""Import boundary checks for the Evidence Harness path."""

from __future__ import annotations

import ast
import unittest

from tests.helpers import project_root


class EvidenceImportBoundaryTest(unittest.TestCase):
    """Keep evidence modules independent from legacy platform modules."""

    def test_evidence_modules_do_not_import_legacy_platform_modules(self) -> None:
        root = project_root()
        evidence_paths = [
            *(root / "checkpoint_ai" / "evidence").glob("*.py"),
            root / "checkpoint_ai" / "harness.py",
        ]
        forbidden = {
            "checkpoint_ai.adapter",
            "checkpoint_ai.agent_config",
            "checkpoint_ai.alerts",
            "checkpoint_ai.autonomy",
            "checkpoint_ai.businessline",
            "checkpoint_ai.external_agents",
            "checkpoint_ai.ha",
            "checkpoint_ai.insights",
            "checkpoint_ai.learning",
            "checkpoint_ai.loop",
            "checkpoint_ai.plugins",
            "checkpoint_ai.runtime",
            "checkpoint_ai.scheduler",
            "checkpoint_ai.templates",
            "checkpoint_ai.workflow",
        }
        violations: list[str] = []

        for path in evidence_paths:
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                module = self._imported_module(node)
                if module is None:
                    continue
                for forbidden_module in forbidden:
                    if module == forbidden_module or module.startswith(f"{forbidden_module}."):
                        violations.append(f"{path.name}: {module}")

        self.assertEqual([], violations)

    def test_evidence_cli_uses_harness_facade(self) -> None:
        """The human CLI should enter through EvidenceHarness, not raw service plumbing."""

        root = project_root()
        cli_path = root / "checkpoint_ai" / "evidence" / "cli.py"
        tree = ast.parse(cli_path.read_text(encoding="utf-8"))
        imported_modules = {
            module for node in ast.walk(tree) if (module := self._imported_module(node)) is not None
        }

        self.assertIn("checkpoint_ai.harness", imported_modules)
        self.assertNotIn("checkpoint_ai.evidence.service", imported_modules)
        self.assertNotIn("checkpoint_ai.evidence.storage", imported_modules)

    @staticmethod
    def _imported_module(node: ast.AST) -> str | None:
        if isinstance(node, ast.ImportFrom):
            return node.module
        if isinstance(node, ast.Import) and node.names:
            return node.names[0].name
        return None


if __name__ == "__main__":
    unittest.main()
