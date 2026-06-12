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
            *(root / "loop_harness" / "evidence").glob("*.py"),
            root / "loop_harness" / "harness.py",
        ]
        forbidden = {
            "loop_harness.adapter",
            "loop_harness.agent_config",
            "loop_harness.alerts",
            "loop_harness.autonomy",
            "loop_harness.businessline",
            "loop_harness.external_agents",
            "loop_harness.ha",
            "loop_harness.insights",
            "loop_harness.learning",
            "loop_harness.loop",
            "loop_harness.plugins",
            "loop_harness.runtime",
            "loop_harness.scheduler",
            "loop_harness.templates",
            "loop_harness.workflow",
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
        cli_path = root / "loop_harness" / "evidence" / "cli.py"
        tree = ast.parse(cli_path.read_text(encoding="utf-8"))
        imported_modules = {
            module for node in ast.walk(tree) if (module := self._imported_module(node)) is not None
        }

        self.assertIn("loop_harness.harness", imported_modules)
        self.assertNotIn("loop_harness.evidence.service", imported_modules)
        self.assertNotIn("loop_harness.evidence.storage", imported_modules)

    @staticmethod
    def _imported_module(node: ast.AST) -> str | None:
        if isinstance(node, ast.ImportFrom):
            return node.module
        if isinstance(node, ast.Import) and node.names:
            return node.names[0].name
        return None


if __name__ == "__main__":
    unittest.main()
