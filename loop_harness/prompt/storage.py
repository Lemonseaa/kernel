"""SQLite storage for prompt versions and proposals."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from loop_harness.prompt.models import (
    PromptPatch,
    PromptProposal,
    PromptProposalStatus,
    PromptSlot,
    PromptVersion,
    Proposal,
    ProposalKind,
    ProposalPatch,
    ProposalStatus,
    ProposalTargetType,
)


class PromptVersionStore:
    """Store complete prompt snapshots and support rollback."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def save_version(
        self,
        scenario_id: str,
        agent_id: str,
        slots: dict[PromptSlot, str] | dict[str, str],
        reason: str,
        parent_version_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> PromptVersion:
        """Save a full prompt snapshot."""

        latest = self.get_latest(scenario_id, agent_id)
        parent_id = parent_version_id if parent_version_id is not None else (latest.id if latest else None)
        version = PromptVersion(
            scenario_id=scenario_id,
            agent_id=agent_id,
            slots={PromptSlot(slot): value for slot, value in slots.items()},
            reason=reason,
            parent_version_id=parent_id,
            metadata=metadata or {},
        )
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO prompt_versions (
                    id, scenario_id, agent_id, slots, reason, parent_version_id, created_at, metadata
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._version_to_row(version),
            )
        return version

    def get_latest(self, scenario_id: str, agent_id: str) -> PromptVersion | None:
        """Return latest prompt version for one scenario and agent."""

        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                """
                SELECT * FROM prompt_versions
                WHERE scenario_id = ? AND agent_id = ?
                ORDER BY created_at DESC, rowid DESC
                LIMIT 1
                """,
                (scenario_id, agent_id),
            ).fetchone()
        return None if row is None else self._version_from_row(row)

    def history(self, scenario_id: str, agent_id: str) -> list[PromptVersion]:
        """Return prompt history ordered by creation."""

        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT * FROM prompt_versions
                WHERE scenario_id = ? AND agent_id = ?
                ORDER BY created_at, rowid
                """,
                (scenario_id, agent_id),
            ).fetchall()
        return [self._version_from_row(row) for row in rows]

    def rollback(self, scenario_id: str, agent_id: str, reason: str) -> PromptVersion:
        """Create a new latest snapshot from the previous version."""

        versions = self.history(scenario_id, agent_id)
        if len(versions) < 2:
            raise ValueError(f"No previous prompt version to rollback: {scenario_id}/{agent_id}")
        previous = versions[-2]
        return self.save_version(
            scenario_id=scenario_id,
            agent_id=agent_id,
            slots=previous.slots,
            reason=f"Rollback: {reason}",
            parent_version_id=previous.id,
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
                CREATE TABLE IF NOT EXISTS prompt_versions (
                    id TEXT PRIMARY KEY,
                    scenario_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    slots TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    parent_version_id TEXT,
                    created_at TEXT NOT NULL,
                    metadata TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_prompt_versions_scenario_agent "
                "ON prompt_versions (scenario_id, agent_id)"
            )

    @staticmethod
    def _version_to_row(version: PromptVersion) -> tuple[Any, ...]:
        return (
            version.id,
            version.scenario_id,
            version.agent_id,
            json.dumps({slot.value: value for slot, value in version.slots.items()}, ensure_ascii=False),
            version.reason,
            version.parent_version_id,
            version.created_at.isoformat(),
            json.dumps(version.metadata, ensure_ascii=False, default=str),
        )

    @staticmethod
    def _version_from_row(row: sqlite3.Row) -> PromptVersion:
        slots = json.loads(row["slots"])
        return PromptVersion(
            id=row["id"],
            scenario_id=row["scenario_id"],
            agent_id=row["agent_id"],
            slots={PromptSlot(slot): value for slot, value in slots.items()},
            reason=row["reason"],
            parent_version_id=row["parent_version_id"],
            created_at=datetime.fromisoformat(row["created_at"]).astimezone(UTC),
            metadata=json.loads(row["metadata"]),
        )


class PromptProposalStore:
    """Store manual prompt patch proposals."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def create(self, proposal: PromptProposal) -> str:
        """Create a proposal. Required fields are enforced by the model."""

        if not proposal.reason.strip() or not proposal.expected_metric.strip():
            raise ValueError("reason and expected_metric are required")
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO prompt_proposals (
                    id, scenario_id, agent_id, patch, reason, expected_metric,
                    status, created_at, updated_at, metadata
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._proposal_to_row(proposal),
            )
        return proposal.id

    def get(self, proposal_id: str) -> PromptProposal | None:
        """Return one proposal by id."""

        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM prompt_proposals WHERE id = ?",
                (proposal_id,),
            ).fetchone()
        return None if row is None else self._proposal_from_row(row)

    def list(
        self,
        status: PromptProposalStatus | None = None,
        scenario_id: str | None = None,
    ) -> list[PromptProposal]:
        """List proposals, optionally filtered by status and scenario."""

        clauses: list[str] = []
        params: list[str] = []
        if status is not None:
            clauses.append("status = ?")
            params.append(status.value)
        if scenario_id is not None:
            clauses.append("scenario_id = ?")
            params.append(scenario_id)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                f"SELECT * FROM prompt_proposals {where} ORDER BY created_at, rowid",
                tuple(params),
            ).fetchall()
        return [self._proposal_from_row(row) for row in rows]

    def update_status(self, proposal_id: str, status: PromptProposalStatus) -> bool:
        """Update proposal status."""

        proposal = self.get(proposal_id)
        if proposal is None:
            return False
        proposal.status = status
        proposal.updated_at = datetime.now(UTC)
        return self.save(proposal)

    def update_metadata(
        self,
        proposal_id: str,
        metadata: dict[str, Any],
    ) -> bool:
        """Merge metadata onto one proposal."""

        proposal = self.get(proposal_id)
        if proposal is None:
            return False
        proposal.metadata = {**proposal.metadata, **metadata}
        proposal.updated_at = datetime.now(UTC)
        return self.save(proposal)

    def save(self, proposal: PromptProposal) -> bool:
        """Persist updates to an existing proposal."""

        with self._connection() as conn:
            cursor = conn.execute(
                """
                UPDATE prompt_proposals
                SET patch = ?,
                    reason = ?,
                    expected_metric = ?,
                    status = ?,
                    updated_at = ?,
                    metadata = ?
                WHERE id = ?
                """,
                (
                    json.dumps(proposal.patch.model_dump(mode="json"), ensure_ascii=False),
                    proposal.reason,
                    proposal.expected_metric,
                    proposal.status.value,
                    proposal.updated_at.isoformat(),
                    json.dumps(proposal.metadata, ensure_ascii=False, default=str),
                    proposal.id,
                ),
            )
            return cursor.rowcount > 0

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
                CREATE TABLE IF NOT EXISTS prompt_proposals (
                    id TEXT PRIMARY KEY,
                    scenario_id TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    patch TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    expected_metric TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata TEXT NOT NULL
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_prompt_proposals_status "
                "ON prompt_proposals (status)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_prompt_proposals_scenario "
                "ON prompt_proposals (scenario_id)"
            )

    @staticmethod
    def _proposal_to_row(proposal: PromptProposal) -> tuple[Any, ...]:
        return (
            proposal.id,
            proposal.scenario_id,
            proposal.agent_id,
            json.dumps(proposal.patch.model_dump(mode="json"), ensure_ascii=False),
            proposal.reason,
            proposal.expected_metric,
            proposal.status.value,
            proposal.created_at.isoformat(),
            proposal.updated_at.isoformat(),
            json.dumps(proposal.metadata, ensure_ascii=False, default=str),
        )

    @staticmethod
    def _proposal_from_row(row: sqlite3.Row) -> PromptProposal:
        return PromptProposal(
            id=row["id"],
            scenario_id=row["scenario_id"],
            agent_id=row["agent_id"],
            patch=PromptPatch(**json.loads(row["patch"])),
            reason=row["reason"],
            expected_metric=row["expected_metric"],
            status=PromptProposalStatus(row["status"]),
            created_at=datetime.fromisoformat(row["created_at"]).astimezone(UTC),
            updated_at=datetime.fromisoformat(row["updated_at"]).astimezone(UTC),
            metadata=json.loads(row["metadata"]),
        )


class ProposalStore:
    """Store generic proposals without replacing legacy PromptProposalStore."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def create(self, proposal: Proposal) -> str:
        """Create a generic proposal."""

        if not proposal.reason.strip() or not proposal.expected_metric.strip():
            raise ValueError("reason and expected_metric are required")
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO proposals (
                    id, scenario_id, proposal_kind, target_type, target_id, patch,
                    reason, expected_metric, status, created_at, updated_at, metadata
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                self._to_row(proposal),
            )
        return proposal.id

    def get(self, proposal_id: str) -> Proposal | None:
        """Return one generic proposal."""

        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute("SELECT * FROM proposals WHERE id = ?", (proposal_id,)).fetchone()
        return None if row is None else self._from_row(row)

    def save(self, proposal: Proposal) -> bool:
        """Persist updates to an existing generic proposal."""

        proposal.updated_at = datetime.now(UTC)
        with self._connection() as conn:
            cursor = conn.execute(
                """
                UPDATE proposals
                SET proposal_kind = ?,
                    target_type = ?,
                    target_id = ?,
                    patch = ?,
                    reason = ?,
                    expected_metric = ?,
                    status = ?,
                    updated_at = ?,
                    metadata = ?
                WHERE id = ?
                """,
                (
                    proposal.proposal_kind.value,
                    proposal.target_type.value,
                    proposal.target_id,
                    json.dumps(proposal.patch.model_dump(mode="json"), ensure_ascii=False, default=str),
                    proposal.reason,
                    proposal.expected_metric,
                    proposal.status.value,
                    proposal.updated_at.isoformat(),
                    json.dumps(proposal.metadata, ensure_ascii=False, default=str),
                    proposal.id,
                ),
            )
            return cursor.rowcount > 0

    def list(
        self,
        status: ProposalStatus | None = None,
        scenario_id: str | None = None,
    ) -> list[Proposal]:
        """List generic proposals."""

        clauses: list[str] = []
        params: list[str] = []
        if status is not None:
            clauses.append("status = ?")
            params.append(status.value)
        if scenario_id is not None:
            clauses.append("scenario_id = ?")
            params.append(scenario_id)
        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                f"SELECT * FROM proposals {where} ORDER BY created_at, rowid",
                tuple(params),
            ).fetchall()
        return [self._from_row(row) for row in rows]

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
                CREATE TABLE IF NOT EXISTS proposals (
                    id TEXT PRIMARY KEY,
                    scenario_id TEXT NOT NULL,
                    proposal_kind TEXT NOT NULL,
                    target_type TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    patch TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    expected_metric TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    metadata TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_proposals_status ON proposals (status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_proposals_scenario ON proposals (scenario_id)")

    @staticmethod
    def _to_row(proposal: Proposal) -> tuple[Any, ...]:
        return (
            proposal.id,
            proposal.scenario_id,
            proposal.proposal_kind.value,
            proposal.target_type.value,
            proposal.target_id,
            json.dumps(proposal.patch.model_dump(mode="json"), ensure_ascii=False, default=str),
            proposal.reason,
            proposal.expected_metric,
            proposal.status.value,
            proposal.created_at.isoformat(),
            proposal.updated_at.isoformat(),
            json.dumps(proposal.metadata, ensure_ascii=False, default=str),
        )

    @staticmethod
    def _from_row(row: sqlite3.Row) -> Proposal:
        return Proposal(
            id=row["id"],
            scenario_id=row["scenario_id"],
            proposal_kind=ProposalKind(row["proposal_kind"]),
            target_type=ProposalTargetType(row["target_type"]),
            target_id=row["target_id"],
            patch=ProposalPatch(**json.loads(row["patch"])),
            reason=row["reason"],
            expected_metric=row["expected_metric"],
            status=ProposalStatus(row["status"]),
            created_at=datetime.fromisoformat(row["created_at"]).astimezone(UTC),
            updated_at=datetime.fromisoformat(row["updated_at"]).astimezone(UTC),
            metadata=json.loads(row["metadata"]),
        )
