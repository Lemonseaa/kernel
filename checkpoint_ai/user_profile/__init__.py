"""User preference profile exports.

User profile is a differentiating CheckpointAI boundary: human methodology,
aesthetic taste, risk preferences, and operating style are explicit inputs.
Agents may suggest drafts, but humans own the formal profile.
"""

from checkpoint_ai.user_profile.models import SuggestedProfileNotes, UserProfileVersion
from checkpoint_ai.user_profile.store import (
    FORMAL_PROFILE_NAME,
    SUGGESTED_NOTES_NAME,
    UserProfileStore,
)

CLEANUP_STATUS = "keep"
REPLACEMENT_PATH = "human-owned methodology and preference profile"

__all__ = [
    "FORMAL_PROFILE_NAME",
    "SUGGESTED_NOTES_NAME",
    "SuggestedProfileNotes",
    "UserProfileStore",
    "UserProfileVersion",
]
