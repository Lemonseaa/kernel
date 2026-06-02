"""Data quality gate for experiment feedback."""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, cast

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from checkpoint_ai.experiment.feedback import Feedback


class QualityStatus(str, Enum):
    """Quality gate decision."""

    PASS = "pass"
    WARN = "warn"
    REJECT = "reject"


class DataQualityResult(BaseModel):
    """Result produced by the data quality gate."""

    status: QualityStatus
    confidence_score: float = Field(ge=0.0, le=1.0)
    issues: list[str] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)


class DataQualityGate:
    """数据质量门控。"""

    _MIN_TIMESTAMP = datetime(2020, 1, 1, tzinfo=UTC)
    _RANGES: dict[str, tuple[float, float, bool, bool]] = {
        "latency": (0.0, 86_400_000.0, False, False),
        "cost": (0.0, float("inf"), True, True),
        "success_rate": (0.0, 1.0, True, True),
        "ic_value": (-1.0, 1.0, True, True),
    }

    def __init__(self, confidence_threshold: float = 0.5) -> None:
        """Create a gate with a configurable confidence threshold."""

        self._confidence_threshold = confidence_threshold

    def validate(self, feedback: Feedback) -> DataQualityResult:
        """校验单条反馈。"""

        issues: list[str] = []
        details: dict[str, Any] = {}
        signal_type = str(getattr(feedback, "signal_type", "")).strip()
        value = getattr(feedback, "value", None)
        timestamp = getattr(feedback, "timestamp", None)

        if not signal_type:
            issues.append("signal_type is required")
            details["missing_signal_type"] = True
        if not self._is_number(value):
            issues.append("value must be numeric")
            details["invalid_value"] = value
        if not isinstance(timestamp, datetime):
            issues.append("timestamp must be datetime")
            details["invalid_timestamp"] = str(timestamp)
        elif timestamp.astimezone(UTC) > datetime.now(UTC):
            issues.append("timestamp cannot be in the future")
            details["future_timestamp"] = timestamp.isoformat()
        elif timestamp.astimezone(UTC) < self._MIN_TIMESTAMP:
            issues.append("timestamp cannot be earlier than 2020")
            details["old_timestamp"] = timestamp.isoformat()

        if issues:
            return DataQualityResult(
                status=QualityStatus.REJECT,
                confidence_score=0.0,
                issues=issues,
                details=details,
            )

        numeric_value = float(cast(float, value))
        if signal_type in self._RANGES and not self._in_range(signal_type, numeric_value):
            details["out_of_range"] = {
                "signal_type": signal_type,
                "value": numeric_value,
                "range": self._RANGES[signal_type],
            }
            return DataQualityResult(
                status=QualityStatus.WARN,
                confidence_score=0.6,
                issues=[f"{signal_type} out of expected range"],
                details=details,
            )

        return DataQualityResult(status=QualityStatus.PASS, confidence_score=0.95, issues=[], details={})

    def validate_batch(self, feedbacks: list[Feedback]) -> list[DataQualityResult]:
        """批量校验。"""

        return [self.validate(feedback) for feedback in feedbacks]

    def get_confidence_threshold(self) -> float:
        """获取当前置信度阈值。"""

        return self._confidence_threshold

    @staticmethod
    def _is_number(value: object) -> bool:
        return isinstance(value, int | float) and not isinstance(value, bool)

    def _in_range(self, signal_type: str, value: float) -> bool:
        lower, upper, lower_inclusive, upper_inclusive = self._RANGES[signal_type]
        lower_ok = value >= lower if lower_inclusive else value > lower
        upper_ok = value <= upper if upper_inclusive else value < upper
        return lower_ok and upper_ok
