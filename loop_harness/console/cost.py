"""Persistent V5 cost event store."""

from __future__ import annotations

import sqlite3
import uuid
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field


class CostEvent(BaseModel):
    """One persisted cost observation."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    scenario_id: str | None = None
    business_line_id: str
    provider: str
    input_tokens: int
    output_tokens: int
    estimated_cost: float
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    @property
    def total_tokens(self) -> int:
        """Return total tokens."""

        return self.input_tokens + self.output_tokens


class DailyCostSummary(BaseModel):
    """Aggregated daily cost summary."""

    provider: str
    business_line_id: str
    input_tokens: int
    output_tokens: int
    estimated_cost: float

    @property
    def total_tokens(self) -> int:
        """Return total tokens."""

        return self.input_tokens + self.output_tokens


class CostEventStore:
    """Persist cost events for restart-safe control panels."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def record(self, event: CostEvent) -> str:
        """Persist one cost event."""

        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO cost_events (
                    id, scenario_id, business_line_id, provider, input_tokens,
                    output_tokens, estimated_cost, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.id,
                    event.scenario_id,
                    event.business_line_id,
                    event.provider,
                    event.input_tokens,
                    event.output_tokens,
                    event.estimated_cost,
                    event.created_at.isoformat(),
                ),
            )
        return event.id

    def daily_summary(
        self,
        provider: str,
        business_line_id: str,
        day: str | None = None,
    ) -> DailyCostSummary:
        """Return daily provider/business-line cost summary."""

        day_key = day or datetime.now(UTC).date().isoformat()
        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT
                    COALESCE(SUM(input_tokens), 0) AS input_tokens,
                    COALESCE(SUM(output_tokens), 0) AS output_tokens,
                    COALESCE(SUM(estimated_cost), 0.0) AS estimated_cost
                FROM cost_events
                WHERE provider = ?
                  AND business_line_id = ?
                  AND substr(created_at, 1, 10) = ?
                """,
                (provider, business_line_id, day_key),
            ).fetchone()
        return DailyCostSummary(
            provider=provider,
            business_line_id=business_line_id,
            input_tokens=int(row["input_tokens"]),
            output_tokens=int(row["output_tokens"]),
            estimated_cost=float(row["estimated_cost"]),
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
                CREATE TABLE IF NOT EXISTS cost_events (
                    id TEXT PRIMARY KEY,
                    scenario_id TEXT,
                    business_line_id TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    input_tokens INTEGER NOT NULL,
                    output_tokens INTEGER NOT NULL,
                    estimated_cost REAL NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_cost_events_provider ON cost_events (provider)")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_cost_events_business_line ON cost_events (business_line_id)"
            )
