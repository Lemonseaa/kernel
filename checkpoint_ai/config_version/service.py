"""Config version manager service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from checkpoint_ai.config_version.models import ConfigBranch, ConfigVersion
from checkpoint_ai.config_version.store import ConfigBranchStore, ConfigVersionStore


class ConfigVersionService:
    """Manage version snapshots and optimization branches."""

    def __init__(self, versions: ConfigVersionStore, branches: ConfigBranchStore) -> None:
        self.versions = versions
        self.branches = branches

    def save_version(
        self,
        scenario_id: str,
        business_line_id: str,
        config: dict[str, Any],
        reason: str,
        parent_version_id: str | None = None,
    ) -> ConfigVersion:
        """Save a full config snapshot."""

        version = ConfigVersion(
            scenario_id=scenario_id,
            business_line_id=business_line_id,
            config=config,
            reason=reason,
            parent_version_id=parent_version_id,
        )
        self.versions.save(version)
        return version

    def lock_version(self, version_id: str, reason: str) -> ConfigVersion:
        """Lock a version so it becomes immutable."""

        version = self._required_version(version_id)
        version.locked = True
        version.locked_reason = reason
        version.updated_at = datetime.now(UTC)
        with self.versions._connection() as conn:  # noqa: SLF001 - service owns this store.
            conn.execute(
                "UPDATE config_versions SET locked = 1, locked_reason = ?, updated_at = ? WHERE id = ?",
                (reason, version.updated_at.isoformat(), version.id),
            )
        return version

    def create_branch(
        self,
        scenario_id: str,
        business_line_id: str,
        name: str,
        base_version_id: str,
    ) -> ConfigBranch:
        """Create an active branch from a locked version."""

        base = self._required_version(base_version_id)
        if not base.locked:
            raise ValueError("branches must be based on a locked version")
        branch = ConfigBranch(
            scenario_id=scenario_id,
            business_line_id=business_line_id,
            name=name,
            base_version_id=base_version_id,
            active=True,
        )
        self.branches.save(branch)
        return branch

    def get_active_branch(self, scenario_id: str) -> ConfigBranch:
        """Return active branch or raise."""

        branch = self.branches.get_active(scenario_id)
        if branch is None:
            raise KeyError(f"No active branch for scenario: {scenario_id}")
        return branch

    def rollback_to_locked(self, scenario_id: str, locked_version_id: str) -> ConfigVersion:
        """Return the locked version used as rollback target."""

        version = self._required_version(locked_version_id)
        if version.scenario_id != scenario_id or not version.locked:
            raise ValueError("rollback target must be a locked version in the same scenario")
        return version

    def _required_version(self, version_id: str) -> ConfigVersion:
        version = self.versions.get(version_id)
        if version is None:
            raise KeyError(f"Config version not found: {version_id}")
        return version
