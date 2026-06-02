"""Risk scoring for experiment actions."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field

from checkpoint_ai.experiment.ledger import ExperimentLedger

DEFAULT_THRESHOLD = 0.6


class RiskScore(BaseModel):
    """Weighted risk score for an action."""

    magnitude_risk: float = Field(ge=0.0, le=1.0)
    blast_radius_risk: float = Field(ge=0.0, le=1.0)
    reversibility_risk: float = Field(ge=0.0, le=1.0)
    confidence_risk: float = Field(ge=0.0, le=1.0)
    policy_risk: float = Field(ge=0.0, le=1.0)
    total: float = Field(ge=0.0, le=1.0)
    requires_human_review: bool
    report: str


class ActionRisk(BaseModel):
    """Action风险评估。"""

    action_type: str
    target: str
    magnitude: float = Field(ge=0.0, le=1.0)
    blast_radius: float | None = Field(default=None)
    reversibility: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(ge=0.0, le=1.0)
    policy_compliant: bool = True


class RiskScorer:
    """风险评分器。"""

    def __init__(self, storage: str | Path | None = None, threshold: float | None = None) -> None:
        """Create a risk scorer with optional SQLite-backed threshold config."""

        self.path = Path(storage) if storage is not None else None
        self._threshold = threshold if threshold is not None else DEFAULT_THRESHOLD
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._init_schema()

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        if self.path is None:
            raise RuntimeError("RiskScorer has no SQLite storage")
        conn = sqlite3.connect(self.path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS risk_config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )

    def score_action(self, action: ActionRisk) -> RiskScore:
        """评估Action风险。"""

        magnitude_risk = action.magnitude
        blast_radius_risk = self._blast_radius(action)
        reversibility_risk = 1.0 - action.reversibility
        confidence_risk = 1.0 - action.confidence
        policy_risk = 0.0 if action.policy_compliant else 1.0
        total = round(
            magnitude_risk * 0.3
            + blast_radius_risk * 0.2
            + reversibility_risk * 0.2
            + confidence_risk * 0.15
            + policy_risk * 0.15,
            4,
        )
        requires_human_review = total > self.get_threshold()
        return RiskScore(
            magnitude_risk=magnitude_risk,
            blast_radius_risk=blast_radius_risk,
            reversibility_risk=reversibility_risk,
            confidence_risk=confidence_risk,
            policy_risk=policy_risk,
            total=total,
            requires_human_review=requires_human_review,
            report=self._report(action, total, requires_human_review),
        )

    def score_experiment(self, experiment_id: str) -> RiskScore:
        """评估实验风险。"""

        if self.path is None:
            raise RuntimeError("score_experiment requires SQLite storage")
        experiment = ExperimentLedger(self.path).get(experiment_id)
        if experiment is None:
            raise KeyError(f"Experiment not found: {experiment_id}")
        metadata = experiment.metadata
        action = ActionRisk(
            action_type=str(metadata.get("action_type", self._infer_action_type(experiment.action))),
            target=str(metadata.get("target", experiment.action)),
            magnitude=self._float_metadata(metadata, "magnitude", 0.1),
            blast_radius=self._optional_float_metadata(metadata, "blast_radius"),
            reversibility=self._float_metadata(metadata, "reversibility", 0.9),
            confidence=self._float_metadata(metadata, "confidence", 0.9),
            policy_compliant=bool(metadata.get("policy_compliant", True)),
        )
        return self.score_action(action)

    def get_threshold(self) -> float:
        """获取风险阈值。"""

        if self.path is None:
            return self._threshold
        with self._connection() as conn:
            row = conn.execute("SELECT value FROM risk_config WHERE key = ?", ("threshold",)).fetchone()
        if row is None:
            return self._threshold
        return float(row[0])

    def set_threshold(self, threshold: float) -> None:
        """Persist the risk review threshold."""

        if not 0.0 <= threshold <= 1.0:
            raise ValueError("threshold must be between 0 and 1")
        self._threshold = threshold
        if self.path is None:
            return
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO risk_config (key, value)
                VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value
                """,
                ("threshold", str(threshold)),
            )

    def should_auto_execute(self, risk_score: RiskScore) -> bool:
        """判断是否应自动执行。"""

        return not risk_score.requires_human_review

    @staticmethod
    def _float_metadata(metadata: dict[str, Any], key: str, default: float) -> float:
        value = metadata.get(key, default)
        return float(value) if isinstance(value, int | float | str) else default

    @staticmethod
    def _optional_float_metadata(metadata: dict[str, Any], key: str) -> float | None:
        value = metadata.get(key)
        return float(value) if isinstance(value, int | float | str) else None

    @staticmethod
    def _blast_radius(action: ActionRisk) -> float:
        if action.blast_radius is not None:
            return action.blast_radius
        defaults = {
            "parameter_tune": 0.425,
            "strategy_switch": 0.95,
            "resource_realloc": 0.7,
        }
        return defaults.get(action.action_type, 0.5)

    @staticmethod
    def _infer_action_type(action: str) -> str:
        if "switch" in action.lower() or "strategy" in action.lower():
            return "strategy_switch"
        if "resource" in action.lower():
            return "resource_realloc"
        return "parameter_tune"

    @staticmethod
    def _report(action: ActionRisk, total: float, requires_human_review: bool) -> str:
        return (
            f"action_type={action.action_type}; target={action.target}; "
            f"magnitude={action.magnitude}; blast_radius={action.blast_radius}; "
            f"reversibility={action.reversibility}; confidence={action.confidence}; "
            f"policy_compliant={action.policy_compliant}; total={total}; "
            f"requires_human_review={requires_human_review}"
        )
