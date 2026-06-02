"""LLM response cache."""

from __future__ import annotations

import hashlib
import time
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class CacheKey:
    """Stable cache key for one prompt and model."""

    prompt_hash: str
    model: str

    @classmethod
    def from_prompt(cls, prompt: str, model: str) -> CacheKey:
        """Build a cache key from prompt text and model name."""

        digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
        return cls(prompt_hash=digest, model=model)


@dataclass(slots=True)
class _CacheEntry:
    """Stored response and its insertion timestamp."""

    response: Any
    created_at: float


class LLMResponseCache:
    """In-memory TTL cache for LLM responses."""

    def __init__(
        self,
        max_size: int = 128,
        ttl_seconds: float = 300.0,
        now: Callable[[], float] | None = None,
    ) -> None:
        """Create a bounded cache."""

        if max_size <= 0:
            raise ValueError("max_size must be greater than zero.")
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be greater than zero.")
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._now = now or time.time
        self._entries: OrderedDict[CacheKey, _CacheEntry] = OrderedDict()
        self._hits = 0
        self._misses = 0

    def get(self, prompt: str, model: str) -> Any | None:
        """Return a cached response, or None when missing or expired."""

        self._purge_expired()
        key = CacheKey.from_prompt(prompt, model)
        entry = self._entries.get(key)
        if entry is None:
            self._misses += 1
            return None
        if self._is_expired(entry):
            self._entries.pop(key, None)
            self._misses += 1
            return None
        self._entries.move_to_end(key)
        self._hits += 1
        return entry.response

    def set(self, prompt: str, model: str, response: Any) -> None:
        """Store a response for a prompt and model."""

        self._purge_expired()
        key = CacheKey.from_prompt(prompt, model)
        self._entries[key] = _CacheEntry(response=response, created_at=self._now())
        self._entries.move_to_end(key)
        while len(self._entries) > self.max_size:
            self._entries.popitem(last=False)

    def stats(self) -> dict[str, float | int]:
        """Return cache size and hit-rate statistics."""

        self._purge_expired()
        total = self._hits + self._misses
        hit_rate = self._hits / total if total else 0.0
        return {
            "size": len(self._entries),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
        }

    def clear(self) -> None:
        """Clear cache entries and counters."""

        self._entries.clear()
        self._hits = 0
        self._misses = 0

    def _purge_expired(self) -> None:
        """Remove expired entries."""

        expired_keys = [key for key, entry in self._entries.items() if self._is_expired(entry)]
        for key in expired_keys:
            self._entries.pop(key, None)

    def _is_expired(self, entry: _CacheEntry) -> bool:
        """Return true when an entry is past its TTL."""

        return self._now() - entry.created_at > self.ttl_seconds
