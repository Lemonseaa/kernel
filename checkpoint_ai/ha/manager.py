"""High availability manager."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass

from checkpoint_ai.events import EventBus
from checkpoint_ai.ha.store import HAStateStore


@dataclass(slots=True)
class HAStatus:
    """Current HA status snapshot."""

    instance_id: str
    role: str
    primary_instance_id: str | None
    lease_expires_at: float | None


class HAManager:
    """Lease-based primary election manager."""

    def __init__(
        self,
        instance_id: str,
        store: HAStateStore,
        lease_ttl_seconds: float = 30.0,
        now: Callable[[], float] | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Create a high availability manager."""

        self.instance_id = instance_id
        self.store = store
        self.lease_ttl_seconds = lease_ttl_seconds
        self._now = now or time.time
        self.event_bus = event_bus

    def try_become_primary(self) -> bool:
        """Try to acquire the primary lease."""

        acquired = self.store.acquire_primary(
            self.instance_id,
            now=self._now(),
            ttl_seconds=self.lease_ttl_seconds,
        )
        if acquired and self.event_bus is not None:
            self.event_bus.emit("ha:primary_acquired", {"instance_id": self.instance_id})
        return acquired

    def heartbeat(self) -> bool:
        """Refresh the lease when this instance is primary."""

        refreshed = self.store.heartbeat(
            self.instance_id,
            now=self._now(),
            ttl_seconds=self.lease_ttl_seconds,
        )
        if refreshed and self.event_bus is not None:
            self.event_bus.emit("ha:heartbeat", {"instance_id": self.instance_id})
        return refreshed

    def is_primary(self) -> bool:
        """Return true when this instance owns the active primary lease."""

        current = self.store.current_primary(now=self._now())
        return current is not None and current.instance_id == self.instance_id

    def status(self) -> HAStatus:
        """Return an HA status snapshot."""

        current = self.store.current_primary(now=self._now())
        primary_instance_id = current.instance_id if current is not None else None
        return HAStatus(
            instance_id=self.instance_id,
            role="primary" if primary_instance_id == self.instance_id else "backup",
            primary_instance_id=primary_instance_id,
            lease_expires_at=current.expires_at if current is not None else None,
        )
