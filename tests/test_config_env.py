"""Environment configuration tests."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from opc_os.config import KernelConfig


def _without_kernel_env() -> dict[str, str]:
    """Return process env without Kernel-specific overrides."""

    return {key: value for key, value in os.environ.items() if not key.startswith("KERNEL_")}


class EnvConfigTest(unittest.TestCase):
    """Validate zero-code configuration loading."""

    def test_kernel_config_loads_values_from_env_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            env_path.write_text(
                "\n".join(
                    [
                        "KERNEL_DEFAULT_PROVIDER=openai",
                        "KERNEL_OPENAI_API_KEY=test-openai",
                        "KERNEL_OPENAI_MODEL=gpt-test",
                        "KERNEL_DB_PATH=/data/kernel.db",
                        "KERNEL_MAX_CONCURRENCY=4",
                        "KERNEL_LLM_CACHE_ENABLED=false",
                        "KERNEL_LLM_CACHE_TTL_SECONDS=42",
                    ]
                ),
                encoding="utf-8",
            )

            with patch.dict(os.environ, _without_kernel_env(), clear=True):
                config = KernelConfig.from_env(env_path=env_path)

        self.assertEqual(config.default_provider, "openai")
        self.assertEqual(config.providers["openai"]["api_key"], "test-openai")
        self.assertEqual(config.providers["openai"]["model"], "gpt-test")
        self.assertEqual(config.sqlite_path, "/data/kernel.db")
        self.assertEqual(config.max_concurrency, 4)
        self.assertFalse(config.llm_cache_enabled)
        self.assertEqual(config.llm_cache_ttl_seconds, 42.0)

    def test_environment_variables_override_env_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            env_path.write_text("KERNEL_DEFAULT_PROVIDER=minimax\n", encoding="utf-8")

            with patch.dict(os.environ, {"KERNEL_DEFAULT_PROVIDER": "openai"}, clear=False):
                config = KernelConfig.from_env(env_path=env_path)

        self.assertEqual(config.default_provider, "openai")


if __name__ == "__main__":
    unittest.main()
