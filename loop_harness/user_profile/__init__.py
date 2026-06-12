"""User preference profile exports.

User profile is a differentiating LoopHarness boundary: human methodology,
aesthetic taste, risk preferences, and operating style are explicit inputs.
Agents may suggest drafts, but humans own the formal profile.
"""

from loop_harness.user_profile.models import SuggestedProfileNotes, UserProfileVersion
from loop_harness.user_profile.store import (
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
