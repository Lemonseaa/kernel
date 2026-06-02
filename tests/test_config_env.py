"""Environment configuration tests."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from opc_os.config import OPCOSConfig


def _without_opc_os_env() -> dict[str, str]:
    """Return process env without OPCOS-specific overrides."""

    return {key: value for key, value in os.environ.items() if not key.startswith("OPC_OS_")}


class EnvConfigTest(unittest.TestCase):
    """Validate zero-code configuration loading."""

    def test_opc_os_config_loads_values_from_env_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            env_path.write_text(
                "\n".join(
                    [
                        "OPC_OS_DEFAULT_PROVIDER=openai",
                        "OPC_OS_OPENAI_API_KEY=test-openai",
                        "OPC_OS_OPENAI_MODEL=gpt-test",
                        "OPC_OS_DB_PATH=/data/opc_os.db",
                        "OPC_OS_MAX_CONCURRENCY=4",
                        "OPC_OS_LLM_CACHE_ENABLED=false",
                        "OPC_OS_LLM_CACHE_TTL_SECONDS=42",
                    ]
                ),
                encoding="utf-8",
            )

            with patch.dict(os.environ, _without_opc_os_env(), clear=True):
                config = OPCOSConfig.from_env(env_path=env_path)

        self.assertEqual(config.default_provider, "openai")
        self.assertEqual(config.providers["openai"]["api_key"], "test-openai")
        self.assertEqual(config.providers["openai"]["model"], "gpt-test")
        self.assertEqual(config.sqlite_path, "/data/opc_os.db")
        self.assertEqual(config.max_concurrency, 4)
        self.assertFalse(config.llm_cache_enabled)
        self.assertEqual(config.llm_cache_ttl_seconds, 42.0)

    def test_environment_variables_override_env_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            env_path.write_text("OPC_OS_DEFAULT_PROVIDER=minimax\n", encoding="utf-8")

            with patch.dict(os.environ, {"OPC_OS_DEFAULT_PROVIDER": "openai"}, clear=False):
                config = OPCOSConfig.from_env(env_path=env_path)

        self.assertEqual(config.default_provider, "openai")


if __name__ == "__main__":
    unittest.main()
