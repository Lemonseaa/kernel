"""Metric schemas and comparison results for V2.10 hardening."""

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MetricDirection(str, Enum):
    """How a metric should move to be considered better."""

    HIGHER = "higher"
    LOWER = "lower"
    REFERENCE = "reference"
    BOUNDED = "bounded"


class MetricCategory(str, Enum):
    """Metric category used to keep business signals clean."""

    BUSINESS = "business"
    SYSTEM = "system"
    DATA_QUALITY = "data_quality"
    GUARDRAIL = "guardrail"


class MetricSchema(BaseModel):
    """One metric definition."""

    name: str
    direction: MetricDirection
    category: MetricCategory = MetricCategory.BUSINESS
    weight: float = 1.0
    threshold: float | None = None
    is_guardrail: bool = False


class MetricEvaluation(BaseModel):
    """Metric-level comparison with direction already applied."""

    name: str
    baseline: float
    candidate: float
    raw_diff: float
    normalized_change: float
    direction: MetricDirection
    category: MetricCategory
    improved: bool


class ComparisonResult(BaseModel):
    """Schema-aware comparison result."""

    metric_diffs: dict[str, float] = Field(default_factory=dict)
    business_metric_diffs: dict[str, float] = Field(default_factory=dict)
    system_metric_diffs: dict[str, float] = Field(default_factory=dict)
    data_quality_metric_diffs: dict[str, float] = Field(default_factory=dict)
    metric_evaluations: dict[str, MetricEvaluation] = Field(default_factory=dict)
    objective_score: float = 0.0
    guardrail_violations: list[str] = Field(default_factory=list)
    improved: bool = False
    summary: str = ""
    run_kind: str = "synthetic"
    provenance: dict[str, Any] = Field(default_factory=dict)


class MetricSchemaRegistry:
    """In-memory metric schema registry."""

    def __init__(self, schemas: list[MetricSchema] | None = None) -> None:
        self._schemas = {schema.name: schema for schema in schemas or []}

    def register(self, schema: MetricSchema) -> None:
        """Register or replace one metric schema."""

        self._schemas[schema.name] = schema

    def get(self, name: str) -> MetricSchema | None:
        """Return a schema by metric name."""

        return self._schemas.get(name)

    def schema_for(self, name: str) -> MetricSchema:
        """Return schema, using safe defaults for known non-business metrics."""

        schema = self.get(name)
        if schema is not None:
            return schema
        if name.endswith("_ms") or name in {"latency_ms"}:
            return MetricSchema(
                name=name,
                direction=MetricDirection.LOWER,
                category=MetricCategory.SYSTEM,
                weight=0.0,
            )
        if name in {"sample_count", "data_quality", "confidence"}:
            return MetricSchema(
                name=name,
                direction=MetricDirection.HIGHER,
                category=MetricCategory.DATA_QUALITY,
                weight=0.0,
            )
        return MetricSchema(name=name, direction=MetricDirection.HIGHER)

    def list(self) -> list[MetricSchema]:
        """List registered metric schemas."""

        return list(self._schemas.values())

    @classmethod
    def default_quant(cls) -> MetricSchemaRegistry:
        """Return the default schema set for quant demo runs."""

        return cls(
            [
                MetricSchema(name="total_return", direction=MetricDirection.HIGHER, weight=0.25),
                MetricSchema(name="annual_return", direction=MetricDirection.HIGHER, weight=0.1),
                MetricSchema(name="benchmark_return", direction=MetricDirection.REFERENCE, weight=0.0),
                MetricSchema(name="excess_return", direction=MetricDirection.HIGHER, weight=0.25),
                MetricSchema(
                    name="max_drawdown",
                    direction=MetricDirection.LOWER,
                    category=MetricCategory.GUARDRAIL,
                    weight=0.2,
                    threshold=0.2,
                    is_guardrail=True,
                ),
                MetricSchema(name="sharpe", direction=MetricDirection.HIGHER, weight=0.3),
                MetricSchema(name="win_rate", direction=MetricDirection.HIGHER, weight=0.05),
                MetricSchema(name="trade_count", direction=MetricDirection.BOUNDED, weight=0.0),
                MetricSchema(name="stability_score", direction=MetricDirection.HIGHER, weight=0.1),
                MetricSchema(
                    name="latency_ms",
                    direction=MetricDirection.LOWER,
                    category=MetricCategory.SYSTEM,
                    weight=0.0,
                ),
                MetricSchema(
                    name="sample_count",
                    direction=MetricDirection.HIGHER,
                    category=MetricCategory.DATA_QUALITY,
                    weight=0.0,
                ),
            ]
        )
