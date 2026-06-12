"""Runtime context assembly for internal Agents."""

from __future__ import annotations

from loop_harness.agent_config.models import AgentRuntimeContext
from loop_harness.user_profile import UserProfileStore


class AgentRuntimeContextBuilder:
    """Build Agent context from human-confirmed sources only."""

    def __init__(self, profile_store: UserProfileStore) -> None:
        self.profile_store = profile_store

    def build(self) -> AgentRuntimeContext:
        """Return profile context with suggested notes separated from formal constraints."""

        return AgentRuntimeContext(
            formal_user_profile=self.profile_store.read_formal_profile(),
            suggested_notes=self.profile_store.read_suggested_notes(),
            metadata={"profile_source": "user/USER_PROFILE.md"},
        )
