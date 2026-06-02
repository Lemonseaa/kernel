"""High availability tests."""

from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from checkpoint_ai.config import CheckpointAIConfig
from checkpoint_ai.ha import HAManager, HAStateStore, SQLiteHAStateStore


def _without_checkpoint_ai_env() -> dict[str, str]:
    """Return process env without CheckpointAI-specific overrides."""

    return {key: value for key, value in os.environ.items() if not key.startswith("CHECKPOINT_AI_")}


class HATest(unittest.TestCase):
    """Validate lease-based high availability behavior."""

    def test_backup_takes_over_after_primary_lease_expires(self) -> None:
        now = 100.0
        store = HAStateStore()
        primary = HAManager("primary", store=store, lease_ttl_seconds=10, now=lambda: now)
        backup = HAManager("backup", store=store, lease_ttl_seconds=10, now=lambda: now)

        self.assertTrue(primary.try_become_primary())
        self.assertFalse(backup.try_become_primary())

        now = 111.0

        self.assertTrue(backup.try_become_primary())
        self.assertFalse(primary.is_primary())
        self.assertTrue(backup.is_primary())

    def test_sqlite_ha_store_shares_state_between_instances(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            db_path = Path(tmp) / "checkpoint_ai.db"
            first_store = SQLiteHAStateStore(db_path)
            second_store = SQLiteHAStateStore(db_path)

            self.assertTrue(first_store.acquire_primary("instance-a", now=100.0, ttl_seconds=10.0))
            self.assertFalse(second_store.acquire_primary("instance-b", now=101.0, ttl_seconds=10.0))
            self.assertTrue(second_store.acquire_primary("instance-b", now=111.0, ttl_seconds=10.0))

    def test_checkpoint_ai_config_loads_ha_settings_from_env(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            env_path.write_text(
                "\n".join(
                    [
                        "CHECKPOINT_AI_HA_ENABLED=true",
                        "CHECKPOINT_AI_INSTANCE_ID=worker-a",
                        "CHECKPOINT_AI_HA_LEASE_TTL_SECONDS=12",
                        "CHECKPOINT_AI_HA_HEARTBEAT_SECONDS=3",
                    ]
                ),
                encoding="utf-8",
            )

            with patch.dict(os.environ, _without_checkpoint_ai_env(), clear=True):
                config = CheckpointAIConfig.from_env(env_path)

        self.assertTrue(config.ha_enabled)
        self.assertEqual(config.instance_id, "worker-a")
        self.assertEqual(config.ha_lease_ttl_seconds, 12.0)
        self.assertEqual(config.ha_heartbeat_seconds, 3.0)


if __name__ == "__main__":
    unittest.main()
