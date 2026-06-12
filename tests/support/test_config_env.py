"""Environment configuration tests."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from loop_harness.config import LoopHarnessConfig


def _without_loop_harness_env() -> dict[str, str]:
    """Return process env without LoopHarness-specific overrides."""

    return {key: value for key, value in os.environ.items() if not key.startswith("LOOP_HARNESS_")}


class EnvConfigTest(unittest.TestCase):
    """Validate zero-code configuration loading."""

    def test_loop_harness_config_loads_values_from_env_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            env_path.write_text(
                "\n".join(
                    [
                        "LOOP_HARNESS_DEFAULT_PROVIDER=openai",
                        "LOOP_HARNESS_OPENAI_API_KEY=test-openai",
                        "LOOP_HARNESS_OPENAI_MODEL=gpt-test",
                        "LOOP_HARNESS_DB_PATH=/data/loop_harness.db",
                        "LOOP_HARNESS_MAX_CONCURRENCY=4",
                        "LOOP_HARNESS_LLM_CACHE_ENABLED=false",
                        "LOOP_HARNESS_LLM_CACHE_TTL_SECONDS=42",
                    ]
                ),
                encoding="utf-8",
            )

            with patch.dict(os.environ, _without_loop_harness_env(), clear=True):
                config = LoopHarnessConfig.from_env(env_path=env_path)

        self.assertEqual(config.default_provider, "openai")
        self.assertEqual(config.providers["openai"]["api_key"], "test-openai")
        self.assertEqual(config.providers["openai"]["model"], "gpt-test")
        self.assertEqual(config.sqlite_path, "/data/loop_harness.db")
        self.assertEqual(config.max_concurrency, 4)
        self.assertFalse(config.llm_cache_enabled)
        self.assertEqual(config.llm_cache_ttl_seconds, 42.0)

    def test_environment_variables_override_env_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            env_path.write_text("LOOP_HARNESS_DEFAULT_PROVIDER=minimax\n", encoding="utf-8")

            with patch.dict(os.environ, {"LOOP_HARNESS_DEFAULT_PROVIDER": "openai"}, clear=False):
                config = LoopHarnessConfig.from_env(env_path=env_path)

        self.assertEqual(config.default_provider, "openai")


if __name__ == "__main__":
    unittest.main()
