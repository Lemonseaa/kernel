"""Authentication exports.

Authentication is a thin boundary for local/API access control. It should not
expand into a full identity platform inside CheckpointAI.
"""

from checkpoint_ai.auth.api_key_manager import APIKeyManager, APIKeyRecord
from checkpoint_ai.auth.bearer_token import BearerTokenAuth

CLEANUP_STATUS = "isolate"
REPLACEMENT_PATH = "thin API auth boundary"

__all__ = ["APIKeyManager", "APIKeyRecord", "BearerTokenAuth"]
