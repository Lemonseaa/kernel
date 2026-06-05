"""File-backed user profile store with SQLite audit history."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from checkpoint_ai.user_profile.models import SuggestedProfileNotes, UserProfileVersion

FORMAL_PROFILE_NAME = "USER_PROFILE.md"
SUGGESTED_NOTES_NAME = "SUGGESTED_PROFILE_NOTES.md"


class UserProfileStore:
    """Manage human-confirmed preferences and Hermes draft notes separately."""

    def __init__(self, profile_dir: str | Path, db_path: str | Path) -> None:
        self.profile_dir = Path(profile_dir)
        self.db_path = Path(db_path)
        self.profile_dir.mkdir(parents=True, exist_ok=True)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_files()
        self._init_schema()

    @property
    def formal_path(self) -> Path:
        """Return formal profile path."""

        return self.profile_dir / FORMAL_PROFILE_NAME

    @property
    def suggested_path(self) -> Path:
        """Return suggested-notes path."""

        return self.profile_dir / SUGGESTED_NOTES_NAME

    def read_formal_profile(self) -> str:
        """Read only the human-confirmed formal profile."""

        return self.formal_path.read_text(encoding="utf-8")

    def read_suggested_notes(self) -> str:
        """Read Hermes/user draft notes."""

        return self.suggested_path.read_text(encoding="utf-8")

    def save_formal_profile(self, content: str, actor: str, reason: str) -> UserProfileVersion:
        """Save formal profile only when the actor is human."""

        if actor != "human":
            raise ValueError("Only human can update USER_PROFILE.md")
        if not reason.strip():
            raise ValueError("formal profile updates require a reason")
        version = UserProfileVersion(actor=actor, reason=reason, content=content)
        self.formal_path.write_text(content, encoding="utf-8")
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO user_profile_versions (id, actor, reason, content, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (version.id, version.actor, version.reason, version.content, version.created_at.isoformat()),
            )
        return version

    def save_suggested_notes(self, content: str, actor: str = "hermes") -> SuggestedProfileNotes:
        """Save non-binding suggested notes."""

        notes = SuggestedProfileNotes(actor=actor, content=content)
        self.suggested_path.write_text(content, encoding="utf-8")
        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO suggested_profile_notes (id, actor, content, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (notes.id, notes.actor, notes.content, notes.created_at.isoformat()),
            )
        return notes

    def list_versions(self) -> list[UserProfileVersion]:
        """List formal profile versions."""

        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT * FROM user_profile_versions ORDER BY created_at, rowid",
            ).fetchall()
        return [
            UserProfileVersion(
                id=row["id"],
                actor=row["actor"],
                reason=row["reason"],
                content=row["content"],
                created_at=datetime.fromisoformat(row["created_at"]).astimezone(UTC),
            )
            for row in rows
        ]

    def _ensure_files(self) -> None:
        if not self.formal_path.exists():
            self.formal_path.write_text(_default_profile(), encoding="utf-8")
        if not self.suggested_path.exists():
            self.suggested_path.write_text(_default_suggested_notes(), encoding="utf-8")

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS user_profile_versions (
                    id TEXT PRIMARY KEY,
                    actor TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS suggested_profile_notes (
                    id TEXT PRIMARY KEY,
                    actor TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )


def _default_profile() -> str:
    return (
        "# User Profile\n\n"
        "This file is the only formal source of user preferences for CheckpointAI agents.\n\n"
        "- Human-owned: only the user edits or confirms this file.\n"
        "- Agents may read it as constraints.\n"
        "- Hermes suggestions must stay in SUGGESTED_PROFILE_NOTES.md until the user copies them here.\n"
    )


def _default_suggested_notes() -> str:
    return (
        "# Suggested Profile Notes\n\n"
        "Draft notes from Hermes or other assistants belong here.\n"
        "They are not formal constraints until the user moves them into USER_PROFILE.md.\n"
    )
