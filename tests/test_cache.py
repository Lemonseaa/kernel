"""Cache tests."""

from __future__ import annotations

import unittest

from opc_os.cache import LLMResponseCache
from opc_os.llm import LLMRequest, LLMResponse, MiniMaxProvider


class ResponseCacheTest(unittest.TestCase):
    """Validate LLM response cache behavior."""

    def test_same_prompt_and_model_hits_cache(self) -> None:
        cache = LLMResponseCache(max_size=10, ttl_seconds=60, now=lambda: 100.0)
        response = LLMResponse(output="first", provider="minimax", model="m1")

        cache.set(prompt="hello", model="m1", response=response)

        self.assertEqual(cache.get(prompt="hello", model="m1"), response)
        self.assertIsNone(cache.get(prompt="hello", model="m2"))
        stats = cache.stats()
        self.assertEqual(stats["hits"], 1)
        self.assertEqual(stats["misses"], 1)
        self.assertEqual(stats["hit_rate"], 0.5)

    def test_cache_entry_expires_after_ttl(self) -> None:
        current_time = 100.0

        def now() -> float:
            return current_time

        cache = LLMResponseCache(max_size=10, ttl_seconds=5, now=now)
        response = LLMResponse(output="first", provider="minimax", model="m1")

        cache.set(prompt="hello", model="m1", response=response)
        current_time = 106.0

        self.assertIsNone(cache.get(prompt="hello", model="m1"))
        self.assertEqual(cache.stats()["size"], 0)

    def test_cache_evicts_oldest_entry_when_full(self) -> None:
        cache = LLMResponseCache(max_size=2, ttl_seconds=60, now=lambda: 100.0)

        cache.set("one", "m1", LLMResponse(output="one", provider="minimax", model="m1"))
        cache.set("two", "m1", LLMResponse(output="two", provider="minimax", model="m1"))
        cache.set("three", "m1", LLMResponse(output="three", provider="minimax", model="m1"))

        self.assertIsNone(cache.get("one", "m1"))
        self.assertIsNotNone(cache.get("two", "m1"))
        self.assertIsNotNone(cache.get("three", "m1"))

    def test_provider_uses_response_cache_for_repeated_prompt(self) -> None:
        calls = 0
        cache = LLMResponseCache(max_size=10, ttl_seconds=60)

        def transport(request: LLMRequest) -> str:
            nonlocal calls
            calls += 1
            return f"generated:{request.prompt}"

        provider = MiniMaxProvider(model="m1", transport=transport, response_cache=cache)

        first = provider.generate(LLMRequest(prompt="hello"))
        second = provider.generate(LLMRequest(prompt="hello"))

        self.assertEqual(first.output, "generated:hello")
        self.assertEqual(second.output, "generated:hello")
        self.assertEqual(calls, 1)
        self.assertEqual(cache.stats()["hits"], 1)


if __name__ == "__main__":
    unittest.main()
