"""Evidence-based recommendation exports.

Recommendations are part of the Evidence Harness only when they are derived
from stored comparisons, metrics, and decision records. They must not become a
free-standing recommendation engine detached from evidence.
"""

from loop_harness.recommendation.models import (
    RecommendationDecision,
    RecommendationStatus,
    VersionRecommendation,
)
from loop_harness.recommendation.recommender import VersionRecommender
from loop_harness.recommendation.store import VersionRecommendationStore

CLEANUP_STATUS = "evidence_support"
REPLACEMENT_PATH = "evidence report recommendation section"

__all__ = [
    "RecommendationDecision",
    "RecommendationStatus",
    "VersionRecommendation",
    "VersionRecommendationStore",
    "VersionRecommender",
]
