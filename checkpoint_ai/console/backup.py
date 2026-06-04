"""SQLite backup and restore utilities for V5."""

from __future__ import annotations

import shutil
import uuid
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, Field


class BackupRecord(BaseModel):
    """One backup artifact."""

    id: str
    label: str
    path: Path
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class BackupManager:
    """Create, list, and restore SQLite database backups."""

    def __init__(self, db_path: str | Path, backup_dir: str | Path) -> None:
        self.db_path = Path(db_path)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, label: str) -> BackupRecord:
        """Create one database backup."""

        backup_id = str(uuid.uuid4())
        safe_label = label.replace(" ", "-")
        target = self.backup_dir / f"{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}__{safe_label}__{backup_id}.db"
        if self.db_path.exists():
            shutil.copy2(self.db_path, target)
        else:
            target.touch()
        return BackupRecord(id=backup_id, label=label, path=target)

    def list_backups(self) -> list[BackupRecord]:
        """List backups ordered by filename."""

        records: list[BackupRecord] = []
        for path in sorted(self.backup_dir.glob("*.db")):
            parts = path.stem.split("__")
            backup_id = parts[-1]
            label = parts[1] if len(parts) > 2 else "backup"
            records.append(BackupRecord(id=backup_id, label=label, path=path))
        return records

    def restore(self, backup_id: str) -> bool:
        """Restore a backup by id, creating a safety backup first."""

        match = next((record for record in self.list_backups() if record.id == backup_id), None)
        if match is None:
            return False
        if self.db_path.exists():
            safety = self.backup_dir / f"{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}__safety__{uuid.uuid4()}.db"
            shutil.copy2(self.db_path, safety)
        shutil.copy2(match.path, self.db_path)
        return True
