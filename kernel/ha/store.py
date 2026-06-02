"""High availability state stores."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class HARecord:
    """Current primary lease record."""

    instance_id: str
    expires_at: float
    heartbeat_at: float


class HAStateStore:
    """In-memory HA lease state store."""

    def __init__(self) -> None:
        """Create an empty HA state store."""

        self._primary: HARecord | None = None

    def acquire_primary(self, instance_id: str, now: float, ttl_seconds: float) -> bool:
        """Acquire the primary lease when absent, expired, or already owned."""

        if self._primary is not None and self._primary.expires_at > now:
            if self._primary.instance_id != instance_id:
                return False
        self._primary = HARecord(
            instance_id=instance_id,
            expires_at=now + ttl_seconds,
            heartbeat_at=now,
        )
        return True

    def heartbeat(self, instance_id: str, now: float, ttl_seconds: float) -> bool:
        """Refresh the primary lease for the owner."""

        if self._primary is None or self._primary.instance_id != instance_id:
            return False
        self._primary = HARecord(
            instance_id=instance_id,
            expires_at=now + ttl_seconds,
            heartbeat_at=now,
        )
        return True

    def current_primary(self, now: float) -> HARecord | None:
        """Return the non-expired current primary lease."""

        if self._primary is None:
            return None
        if self._primary.expires_at <= now:
            return None
        return self._primary


class SQLiteHAStateStore(HAStateStore):
    """SQLite-backed HA lease store shared by multiple instances."""

    def __init__(self, sqlite_path: str | Path) -> None:
        """Create a SQLite HA state store."""

        self.sqlite_path = Path(sqlite_path)
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def acquire_primary(self, instance_id: str, now: float, ttl_seconds: float) -> bool:
        """Acquire the primary lease when current lease is absent or expired."""

        with self._connection() as connection:
            current = self._current_primary(connection)
            if current is not None and current.expires_at > now and current.instance_id != instance_id:
                return False
            self._upsert_primary(connection, instance_id, now, ttl_seconds)
            return True

    def heartbeat(self, instance_id: str, now: float, ttl_seconds: float) -> bool:
        """Refresh the primary lease for the owner."""

        with self._connection() as connection:
            current = self._current_primary(connection)
            if current is None or current.instance_id != instance_id:
                return False
            self._upsert_primary(connection, instance_id, now, ttl_seconds)
            return True

    def current_primary(self, now: float) -> HARecord | None:
        """Return the non-expired current primary lease."""

        with self._connection() as connection:
            current = self._current_primary(connection)
        if current is None or current.expires_at <= now:
            return None
        return current

    def _init_schema(self) -> None:
        """Create HA schema."""

        with self._connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS ha_leases (
                    role TEXT PRIMARY KEY,
                    instance_id TEXT NOT NULL,
                    expires_at REAL NOT NULL,
                    heartbeat_at REAL NOT NULL
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        """Open a SQLite connection."""

        return sqlite3.connect(self.sqlite_path)

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        """Open and close a SQLite connection."""

        connection = self._connect()
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def _current_primary(self, connection: sqlite3.Connection) -> HARecord | None:
        """Load current primary lease."""

        row = connection.execute(
            "SELECT instance_id, expires_at, heartbeat_at FROM ha_leases WHERE role = 'primary'"
        ).fetchone()
        if row is None:
            return None
        return HARecord(instance_id=str(row[0]), expires_at=float(row[1]), heartbeat_at=float(row[2]))

    def _upsert_primary(
        self,
        connection: sqlite3.Connection,
        instance_id: str,
        now: float,
        ttl_seconds: float,
    ) -> None:
        """Store primary lease."""

        connection.execute(
            """
            INSERT INTO ha_leases(role, instance_id, expires_at, heartbeat_at)
            VALUES ('primary', ?, ?, ?)
            ON CONFLICT(role) DO UPDATE SET
                instance_id = excluded.instance_id,
                expires_at = excluded.expires_at,
                heartbeat_at = excluded.heartbeat_at
            """,
            (instance_id, now + ttl_seconds, now),
        )
