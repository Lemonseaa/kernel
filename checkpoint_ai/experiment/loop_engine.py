"""Loop engine for continuous experiment ticks."""

from __future__ import annotations

import json
import sqlite3
import time
from collections.abc import Callable, Iterator, Sequence
from contextlib import contextmanager
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from checkpoint_ai.experiment.baseline import BaselineManager
from checkpoint_ai.experiment.data_quality import DataQualityGate
from checkpoint_ai.experiment.feedback import Feedback, FeedbackCollector
from checkpoint_ai.experiment.ledger import ExperimentLedger
from checkpoint_ai.experiment.models import Experiment, ExperimentStatus
from checkpoint_ai.experiment.risk_score import ActionRisk, RiskScorer


class TickStatus(str, Enum):
    """Loop tick lifecycle status."""

    COLLECTED = "collected"
    DATA_VALIDATED = "data_validated"
    ANALYZED = "analyzed"
    ACTION_PROPOSED = "action_proposed"
    RISK_SCORED = "risk_scored"
    SIMULATED = "simulated"
    SHADOWED = "shadowed"
    LIVE_CANDIDATE = "live_candidate"
    EVALUATED = "evaluated"
    CHECKPOINTED = "checkpointed"


class Tick(BaseModel):
    """A persisted loop tick."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    business_line_id: str | None = None
    status: TickStatus
    experiment_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    duration_ms: int = 0
    inputs: dict[str, Any] = Field(default_factory=dict)
    outputs: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    summary: str


class DefaultAnalyzer:
    """Default no-domain analyzer for validated feedback."""

    def analyze(self, validated: Sequence[Any]) -> dict[str, Any]:
        """Return minimal analysis."""

        return {"validated_count": len(validated), "trend": "baseline"}


class DefaultAgent:
    """Default action proposer."""

    def propose(self, analysis: dict[str, Any]) -> ActionRisk:
        """Propose a small parameter tune action."""

        return ActionRisk(
            action_type="parameter_tune",
            target="loop-default",
            magnitude=0.1,
            reversibility=0.9,
            confidence=0.9,
            policy_compliant=True,
        )


class DefaultScheduler:
    """Default scheduler facade."""

    def execute(self, action: ActionRisk) -> dict[str, Any]:
        """Record a simulated execution."""

        return {"mode": "simulated", "target": action.target}

    def mark_live_candidate(self, action: ActionRisk) -> dict[str, Any]:
        """Record a candidate action requiring review."""

        return {"mode": "live_candidate", "target": action.target}


class DefaultEvaluator:
    """Default evaluator facade."""

    def evaluate(self, action: ActionRisk) -> dict[str, Any]:
        """Return a deterministic result snapshot."""

        return {"target": action.target, "score": 1.0 - action.magnitude}


class LoopEngine:
    """永续循环引擎。"""

    def __init__(
        self,
        collector: FeedbackCollector,
        data_quality: DataQualityGate,
        analyzer: Any,
        agent: Any,
        risk_scorer: RiskScorer,
        scheduler: Any,
        evaluator: Any,
        baseline_manager: BaselineManager,
        ledger: ExperimentLedger,
    ) -> None:
        """Create a loop engine from injected components."""

        self.collector = collector
        self.data_quality = data_quality
        self.analyzer = analyzer
        self.agent = agent
        self.risk_scorer = risk_scorer
        self.scheduler = scheduler
        self.evaluator = evaluator
        self.baseline_manager = baseline_manager
        self.ledger = ledger
        self.path = ledger._storage_path()
        self._tick_callbacks: list[Callable[[Tick], None]] = []
        self._error_callbacks: list[Callable[[Exception], None]] = []
        self._init_schema()

    @classmethod
    def default(cls, storage: str | Path) -> LoopEngine:
        """Create a default LoopEngine using existing experiment components."""

        path = Path(storage)
        return cls(
            collector=FeedbackCollector(path),
            data_quality=DataQualityGate(),
            analyzer=DefaultAnalyzer(),
            agent=DefaultAgent(),
            risk_scorer=RiskScorer(path),
            scheduler=DefaultScheduler(),
            evaluator=DefaultEvaluator(),
            baseline_manager=BaselineManager(path),
            ledger=ExperimentLedger(path),
        )

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
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
                CREATE TABLE IF NOT EXISTS loop_ticks (
                    id TEXT PRIMARY KEY,
                    business_line_id TEXT,
                    status TEXT NOT NULL,
                    experiment_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    duration_ms INTEGER NOT NULL,
                    inputs TEXT NOT NULL,
                    outputs TEXT NOT NULL,
                    errors TEXT NOT NULL,
                    summary TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS loop_state (
                    business_line_id TEXT PRIMARY KEY,
                    state TEXT NOT NULL,
                    tick_interval INTEGER NOT NULL,
                    updated_at TEXT NOT NULL,
                    last_tick_id TEXT
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_loop_ticks_bl ON loop_ticks (business_line_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_loop_ticks_time ON loop_ticks (timestamp)")

    def start(self, business_line_id: str | None = None, tick_interval: int = 60) -> Tick:
        """启动循环。"""

        self._save_state("running", business_line_id, tick_interval)
        return self.tick(reason="Loop started", business_line_id=business_line_id)

    def stop(self, business_line_id: str | None = None) -> None:
        """停止循环。"""

        interval = int(self.get_status(business_line_id).get("tick_interval", 60))
        self._save_state("stopped", business_line_id, interval)

    def pause(self, business_line_id: str | None = None) -> None:
        """暂停。"""

        interval = int(self.get_status(business_line_id).get("tick_interval", 60))
        self._save_state("paused", business_line_id, interval)

    def resume(self, business_line_id: str | None = None) -> None:
        """恢复。"""

        interval = int(self.get_status(business_line_id).get("tick_interval", 60))
        self._save_state("running", business_line_id, interval)

    def get_status(self, business_line_id: str | None = None) -> dict[str, Any]:
        """获取状态。"""

        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM loop_state WHERE business_line_id = ?",
                (self._state_key(business_line_id),),
            ).fetchone()
        if row is None:
            return {
                "business_line_id": business_line_id,
                "state": "stopped",
                "tick_interval": 60,
                "updated_at": None,
                "last_tick_id": None,
            }
        return {
            "business_line_id": None if row["business_line_id"] == "__default__" else row["business_line_id"],
            "state": row["state"],
            "tick_interval": row["tick_interval"],
            "updated_at": row["updated_at"],
            "last_tick_id": row["last_tick_id"],
        }

    def get_last_tick(self, business_line_id: str | None = None) -> Tick | None:
        """获取上一个tick。"""

        ticks = self.history(limit=1, business_line_id=business_line_id)
        return ticks[0] if ticks else None

    def history(self, limit: int = 10, business_line_id: str | None = None) -> list[Tick]:
        """Return persisted tick history."""

        clauses: list[str] = []
        params: list[Any] = []
        if business_line_id is not None:
            clauses.append("business_line_id = ?")
            params.append(business_line_id)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        params.append(limit)
        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                f"SELECT * FROM loop_ticks {where} ORDER BY timestamp DESC, rowid DESC LIMIT ?",
                tuple(params),
            ).fetchall()
        return [self._tick_from_row(row) for row in rows]

    def tick(self, reason: str = "scheduled tick", business_line_id: str | None = None) -> Tick:
        """Run one explainable loop tick."""

        start = time.perf_counter()
        errors: list[str] = []
        status = TickStatus.COLLECTED
        inputs: dict[str, Any] = {"reason": reason}
        outputs: dict[str, Any] = {}
        experiment_id = ""
        try:
            feedbacks = self._collect_recent()
            outputs["feedback_count"] = len(feedbacks)
            status = TickStatus.DATA_VALIDATED
            validated = self.data_quality.validate_batch(feedbacks)
            outputs["validated_count"] = len(validated)
            status = TickStatus.ANALYZED
            analysis = self.analyzer.analyze(validated)
            outputs["analysis"] = analysis
            status = TickStatus.ACTION_PROPOSED
            action = self.agent.propose(analysis)
            outputs["action"] = action.model_dump()
            status = TickStatus.RISK_SCORED
            risk = self.risk_scorer.score_action(action)
            outputs["risk"] = risk.model_dump()
            if self.risk_scorer.should_auto_execute(risk):
                status = TickStatus.SIMULATED
                outputs["schedule"] = self.scheduler.execute(action)
            else:
                status = TickStatus.LIVE_CANDIDATE
                outputs["schedule"] = self.scheduler.mark_live_candidate(action)
            status = TickStatus.EVALUATED
            result = self.evaluator.evaluate(action)
            outputs["evaluation"] = result
            experiment_id = self._record_experiment(business_line_id, action, risk, result, reason)
            self.baseline_manager.create(
                {"loop_score": result.get("score", 0.0)},
                name=f"loop-checkpoint-{experiment_id[:8]}",
                business_line_id=business_line_id,
                experiment_id=experiment_id,
            )
            status = TickStatus.CHECKPOINTED
        except Exception as exc:
            errors.append(str(exc))
            self._notify_error(exc)
        duration_ms = int((time.perf_counter() - start) * 1000)
        if not experiment_id:
            experiment_id = self._record_failed_experiment(business_line_id, reason, errors)
        tick = Tick(
            business_line_id=business_line_id,
            status=status,
            experiment_id=experiment_id,
            duration_ms=duration_ms,
            inputs=inputs,
            outputs=outputs,
            errors=errors,
            summary=f"{reason}; status={status.value}; feedback={outputs.get('feedback_count', 0)}",
        )
        self._save_tick(tick)
        self._save_state(
            self.get_status(business_line_id).get("state", "running"),
            business_line_id,
            int(self.get_status(business_line_id).get("tick_interval", 60)),
            tick.id,
        )
        if not errors:
            self._notify_tick_complete(tick)
        return tick

    def trigger(self, event: str, data: dict[str, Any]) -> Tick | None:
        """外部事件触发tick。"""

        business_line_id = data.get("business_line_id")
        status = self.get_status(business_line_id)
        if status["state"] == "paused":
            return None
        if status["state"] == "stopped":
            self._save_state("running", business_line_id, int(status["tick_interval"]))
        return self.tick(reason=f"event={event}", business_line_id=business_line_id)

    def on_tick_complete(self, callback: Callable[[Tick], None]) -> None:
        """tick完成回调。"""

        self._tick_callbacks.append(callback)

    def on_error(self, callback: Callable[[Exception], None]) -> None:
        """错误回调。"""

        self._error_callbacks.append(callback)

    def _collect_recent(self) -> list[Feedback]:
        return self.collector.list()

    def _record_experiment(
        self,
        business_line_id: str | None,
        action: ActionRisk,
        risk: Any,
        result: dict[str, Any],
        reason: str,
    ) -> str:
        experiment = Experiment(
            business_line_id=business_line_id,
            hypothesis=f"Loop tick proposed {action.action_type} because {reason}.",
            action=f"{action.action_type}:{action.target}",
            before_metrics={},
            after_metrics={"loop_score": result.get("score", 0.0)},
            result_summary=f"Loop evaluated action with risk={risk.total}.",
            status=ExperimentStatus.COMPLETED,
            metadata={
                "loop_reason": reason,
                "action_type": action.action_type,
                "target": action.target,
                "magnitude": action.magnitude,
                "blast_radius": action.blast_radius,
                "reversibility": action.reversibility,
                "confidence": action.confidence,
                "policy_compliant": action.policy_compliant,
            },
        )
        experiment_id = self.ledger.create(experiment)
        self.ledger.update(experiment_id, metadata={**experiment.metadata, "loop_tick_id": "pending"})
        return experiment_id

    def _record_failed_experiment(
        self,
        business_line_id: str | None,
        reason: str,
        errors: list[str],
    ) -> str:
        experiment = Experiment(
            business_line_id=business_line_id,
            hypothesis=f"Loop tick failed because {reason}.",
            action="loop_failed",
            before_metrics={},
            after_metrics={},
            result_summary="; ".join(errors) if errors else "Loop failed.",
            status=ExperimentStatus.FAILED,
            metadata={"loop_reason": reason, "errors": errors},
        )
        return self.ledger.create(experiment)

    def _save_tick(self, tick: Tick) -> None:
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO loop_ticks (
                    id, business_line_id, status, experiment_id, timestamp,
                    duration_ms, inputs, outputs, errors, summary
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    tick.id,
                    tick.business_line_id,
                    tick.status.value,
                    tick.experiment_id,
                    tick.timestamp.isoformat(),
                    tick.duration_ms,
                    json.dumps(tick.inputs, ensure_ascii=False, default=str),
                    json.dumps(tick.outputs, ensure_ascii=False, default=str),
                    json.dumps(tick.errors, ensure_ascii=False, default=str),
                    tick.summary,
                ),
            )
        experiment = self.ledger.get(tick.experiment_id)
        if experiment is not None:
            self.ledger.update(tick.experiment_id, metadata={**experiment.metadata, "loop_tick_id": tick.id})

    def _save_state(
        self,
        state: str,
        business_line_id: str | None,
        tick_interval: int,
        last_tick_id: str | None = None,
    ) -> None:
        current = self.get_status(business_line_id)
        stored_last_tick_id = last_tick_id if last_tick_id is not None else current.get("last_tick_id")
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO loop_state (
                    business_line_id, state, tick_interval, updated_at, last_tick_id
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(business_line_id) DO UPDATE SET
                    state=excluded.state,
                    tick_interval=excluded.tick_interval,
                    updated_at=excluded.updated_at,
                    last_tick_id=excluded.last_tick_id
                """,
                (
                    self._state_key(business_line_id),
                    state,
                    tick_interval,
                    datetime.now(UTC).isoformat(),
                    stored_last_tick_id,
                ),
            )

    @staticmethod
    def _state_key(business_line_id: str | None) -> str:
        return business_line_id or "__default__"

    @staticmethod
    def _tick_from_row(row: sqlite3.Row) -> Tick:
        return Tick(
            id=row["id"],
            business_line_id=row["business_line_id"],
            status=TickStatus(row["status"]),
            experiment_id=row["experiment_id"],
            timestamp=datetime.fromisoformat(row["timestamp"]).astimezone(UTC),
            duration_ms=row["duration_ms"],
            inputs=json.loads(row["inputs"]),
            outputs=json.loads(row["outputs"]),
            errors=json.loads(row["errors"]),
            summary=row["summary"],
        )

    def _notify_tick_complete(self, tick: Tick) -> None:
        for callback in self._tick_callbacks:
            callback(tick)

    def _notify_error(self, error: Exception) -> None:
        for callback in self._error_callbacks:
            callback(error)
