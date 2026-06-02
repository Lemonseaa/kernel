"""Runtime token cost tracking."""

from __future__ import annotations

from dataclasses import dataclass

from kernel.events import EventBus


DEFAULT_BUSINESS_LINE_ID = "default"


@dataclass(slots=True)
class TokenCounter:
    """Accumulated token usage."""

    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        """Return total input and output tokens."""

        return self.input_tokens + self.output_tokens


@dataclass(slots=True)
class CostBreakdown:
    """Provider cost usage summary."""

    provider: str
    input_tokens: int = 0
    output_tokens: int = 0
    business_line_id: str = DEFAULT_BUSINESS_LINE_ID

    @property
    def total_tokens(self) -> int:
        """Return total input and output tokens."""

        return self.input_tokens + self.output_tokens


class CostTracker:
    """Track token usage and publish runtime cost events."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        """Create a cost tracker."""

        self._event_bus = event_bus
        self._counters: dict[tuple[str, str], TokenCounter] = {}
        self._budgets: dict[tuple[str, str], float] = {}

    def set_budget(
        self,
        provider: str,
        daily_budget: float,
        business_line_id: str = DEFAULT_BUSINESS_LINE_ID,
    ) -> None:
        """Set an estimated daily budget for a provider and BusinessLine."""

        self._budgets[(business_line_id, provider)] = daily_budget

    def track(
        self,
        provider: str,
        input_tokens: int,
        output_tokens: int,
        business_line_id: str = DEFAULT_BUSINESS_LINE_ID,
    ) -> None:
        """Record token usage and emit cost events."""

        key = (business_line_id, provider)
        counter = self._counters.setdefault(key, TokenCounter())
        counter.input_tokens += input_tokens
        counter.output_tokens += output_tokens
        current = self._estimate_cost(provider, business_line_id)
        self._emit(
            "cost.updated",
            {
                "provider": provider,
                "business_line_id": business_line_id,
                "input_tokens": counter.input_tokens,
                "output_tokens": counter.output_tokens,
                "total_tokens": counter.total_tokens,
                "current": current,
            },
        )
        budget = self._budgets.get(key)
        if budget is not None and current > budget:
            self._emit(
                "cost.budget_exceeded",
                {
                    "provider": provider,
                    "business_line_id": business_line_id,
                    "budget": budget,
                    "current": current,
                },
            )

    def get_cost(
        self,
        provider: str | None = None,
        business_line_id: str | None = None,
    ) -> CostBreakdown | dict[tuple[str, str], CostBreakdown]:
        """Return one scoped cost summary or all summaries."""

        if provider is not None:
            if business_line_id is None:
                matching = [
                    counter
                    for key, counter in self._counters.items()
                    if key[1] == provider
                ]
                counter = TokenCounter(
                    input_tokens=sum(item.input_tokens for item in matching),
                    output_tokens=sum(item.output_tokens for item in matching),
                )
                line_id = "*"
            else:
                line_id = business_line_id
                counter = self._counters.get((line_id, provider), TokenCounter())
            return CostBreakdown(
                provider=provider,
                input_tokens=counter.input_tokens,
                output_tokens=counter.output_tokens,
                business_line_id=line_id,
            )
        return {
            key: CostBreakdown(
                provider=key[1],
                business_line_id=key[0],
                input_tokens=counter.input_tokens,
                output_tokens=counter.output_tokens,
            )
            for key, counter in self._counters.items()
        }

    def reset(self, provider: str | None = None, business_line_id: str | None = None) -> None:
        """Reset cost counters globally or for one scope."""

        if provider is None and business_line_id is None:
            self._counters.clear()
            return
        keys_to_delete = [
            key
            for key in self._counters
            if (provider is None or key[1] == provider)
            and (business_line_id is None or key[0] == business_line_id)
        ]
        for key in keys_to_delete:
            self._counters.pop(key, None)

    def _estimate_cost(self, provider: str, business_line_id: str) -> float:
        """Estimate cost until the pricing engine exists."""

        counter = self._counters.get((business_line_id, provider), TokenCounter())
        return counter.total_tokens * 0.001

    def _emit(self, event_type: str, payload: dict[str, object]) -> None:
        """Publish an event if an EventBus is configured."""

        if self._event_bus is not None:
            self._event_bus.emit(event_type, payload)
