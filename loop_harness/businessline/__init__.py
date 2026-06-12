"""BusinessLine exports.

BusinessLine remains a coarse business/domain boundary. It is not a tenant
platform and should not drive complex enterprise isolation work unless the
evidence harness needs it.
"""

from loop_harness.businessline.models import (
    BusinessLine,
    BusinessLineConfig,
    BusinessLineStatus,
    ResourceLimits,
)
from loop_harness.businessline.registry import BusinessLineRegistry

CLEANUP_STATUS = "isolate"
REPLACEMENT_PATH = "coarse business/domain boundary"

__all__ = [
    "BusinessLine",
    "BusinessLineConfig",
    "BusinessLineRegistry",
    "BusinessLineStatus",
    "ResourceLimits",
]
