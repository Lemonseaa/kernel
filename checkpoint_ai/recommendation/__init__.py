"""Evidence-based recommendation exports.

Recommendations are part of the Evidence Harness only when they are derived
from stored comparisons, metrics, and decision records. They must not become a
free-standing recommendation engine detached from evidence.
"""

from checkpoint_ai.recommendation.models import (
    RecommendationDecision,
    RecommendationStatus,
    VersionRecommendation,
)
from checkpoint_ai.recommendation.recommender import VersionRecommender
from checkpoint_ai.recommendation.store import VersionRecommendationStore

CLEANUP_STATUS = "evidence_support"
REPLACEMENT_PATH = "evidence report recommendation section"

__all__ = [
    "RecommendationDecision",
    "RecommendationStatus",
    "VersionRecommendation",
    "VersionRecommendationStore",
    "VersionRecommender",
]
