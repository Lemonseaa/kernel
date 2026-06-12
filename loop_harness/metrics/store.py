"""SQLite storage for scenario-specific metric schemas."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from loop_harness.metrics.schema import (
    MetricCategory,
    MetricDirection,
    MetricSchema,
    MetricSchemaRegistry,
)


class MetricSchemaStore:
    """Persist metric schemas per scenario."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def save_for_scenario(self, scenario_id: str, schemas: list[MetricSchema]) -> None:
        """Replace scenario schemas with the provided schema list."""

        now = datetime.now(UTC).isoformat()
        with self._connection() as conn:
            conn.execute("DELETE FROM scenario_metric_schemas WHERE scenario_id = ?", (scenario_id,))
            conn.executemany(
                """
                INSERT INTO scenario_metric_schemas (
                    scenario_id, name, direction, category, weight, threshold,
                    is_guardrail, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        scenario_id,
                        schema.name,
                        schema.direction.value,
                        schema.category.value,
                        schema.weight,
                        schema.threshold,
                        1 if schema.is_guardrail else 0,
                        now,
                        now,
                    )
                    for schema in schemas
                ],
            )

    def list_for_scenario(self, scenario_id: str) -> list[MetricSchema]:
        """List schemas for one scenario."""

        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT * FROM scenario_metric_schemas
                WHERE scenario_id = ?
                ORDER BY name
                """,
                (scenario_id,),
            ).fetchall()
        return [self._from_row(row) for row in rows]

    def registry_for_scenario(self, scenario_id: str) -> MetricSchemaRegistry:
        """Return an in-memory registry for one scenario."""

        return MetricSchemaRegistry(self.list_for_scenario(scenario_id))

    def delete_for_scenario(self, scenario_id: str, metric_name: str | None = None) -> int:
        """Delete scenario schemas."""

        params: tuple[str, ...]
        if metric_name is None:
            sql = "DELETE FROM scenario_metric_schemas WHERE scenario_id = ?"
            params = (scenario_id,)
        else:
            sql = "DELETE FROM scenario_metric_schemas WHERE scenario_id = ? AND name = ?"
            params = (scenario_id, metric_name)
        with self._connection() as conn:
            cursor = conn.execute(sql, params)
            return cursor.rowcount

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
                CREATE TABLE IF NOT EXISTS scenario_metric_schemas (
                    scenario_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    category TEXT NOT NULL,
                    weight REAL NOT NULL,
                    threshold REAL,
                    is_guardrail INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (scenario_id, name)
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_scenario_metric_schemas_scenario "
                "ON scenario_metric_schemas (scenario_id)"
            )

    @staticmethod
    def _from_row(row: sqlite3.Row) -> MetricSchema:
        return MetricSchema(
            name=row["name"],
            direction=MetricDirection(row["direction"]),
            category=MetricCategory(row["category"]),
            weight=row["weight"],
            threshold=row["threshold"],
            is_guardrail=bool(row["is_guardrail"]),
        )
