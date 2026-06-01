"""Dry run LLM provider."""

from __future__ import annotations

from kernel.llm import LLMProvider, LLMRequest, LLMResponse


class DryRunProvider(LLMProvider):
    """Deterministic provider that simulates LLM generation."""

    name = "dryrun"

    def generate(self, request: LLMRequest) -> LLMResponse:
        """Return a simulated response without external API calls."""

        output = self._fallback_output(request)
        return LLMResponse(
            output=output,
            provider=self.name,
            model=self.model or "dryrun",
            metadata={"dry_run": True, "prompt_length": len(request.prompt)},
        )

    def _fallback_output(self, request: LLMRequest) -> str:
        """Return a deterministic preview output."""

        return f"[DRY RUN] Simulated LLM response for: {request.prompt}"
