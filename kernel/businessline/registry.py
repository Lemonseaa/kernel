"""BusinessLine registry."""

from __future__ import annotations

import time

from kernel.businessline.models import BusinessLine, BusinessLineConfig, BusinessLineStatus
from kernel.persistence.store import Storage


class BusinessLineRegistry:
    """Create, cache, and persist BusinessLine records."""

    def __init__(self, storage: Storage) -> None:
        """Create a BusinessLine registry backed by storage."""

        self._storage = storage
        self._cache: dict[str, BusinessLine] = {}

    def create(self, name: str, config: BusinessLineConfig | None = None) -> BusinessLine:
        """Create a BusinessLine. Completed creation enters ACTIVE immediately."""

        business_line = BusinessLine(name=name, config=config or BusinessLineConfig())
        self._storage.save_business_line(business_line)
        self._cache[business_line.id] = business_line
        return business_line

    def get(self, business_line_id: str) -> BusinessLine:
        """Return one BusinessLine by id."""

        if business_line_id in self._cache:
            return self._cache[business_line_id]
        business_line = self._storage.load_business_line(business_line_id)
        self._cache[business_line.id] = business_line
        return business_line

    def list(self, status: BusinessLineStatus | str | None = None) -> list[BusinessLine]:
        """List BusinessLines, optionally filtered by lifecycle status."""

        expected_status = self._coerce_status(status) if status is not None else None
        business_lines = self._storage.list_business_lines(expected_status)
        for business_line in business_lines:
            self._cache[business_line.id] = business_line
        return business_lines

    def update_status(self, business_line_id: str, status: BusinessLineStatus | str) -> BusinessLine:
        """Update lifecycle status and persist it."""

        business_line = self.get(business_line_id)
        business_line.status = self._coerce_status(status)
        business_line.last_active_at = time.time()
        self._storage.save_business_line(business_line)
        self._cache[business_line.id] = business_line
        return business_line

    def delete(self, business_line_id: str) -> BusinessLine:
        """Soft-delete a BusinessLine so audit history remains available."""

        return self.update_status(business_line_id, BusinessLineStatus.DELETED)

    @staticmethod
    def _coerce_status(status: BusinessLineStatus | str) -> BusinessLineStatus:
        """Normalize status strings and enums."""

        if isinstance(status, BusinessLineStatus):
            return status
        return BusinessLineStatus(status)
