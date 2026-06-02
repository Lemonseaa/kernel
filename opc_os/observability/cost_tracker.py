"""Runtime token cost tracking."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Callable

from opc_os.events import EventBus

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

    def __init__(
        self,
        event_bus: EventBus | None = None,
        today_provider: Callable[[], date] | None = None,
    ) -> None:
        """Create a cost tracker."""

        self._event_bus = event_bus
        self._today_provider = today_provider or date.today
        self._counters: dict[tuple[str, str], TokenCounter] = {}
        self._daily_counters: dict[tuple[str, str, str], TokenCounter] = {}
        self._budgets: dict[tuple[str, str], float] = {}
        self._warning_days: set[tuple[str, str, str]] = set()

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

        day = self._today().isoformat()
        key = (business_line_id, provider)
        counter = self._counters.setdefault(key, TokenCounter())
        counter.input_tokens += input_tokens
        counter.output_tokens += output_tokens
        daily_key = (day, business_line_id, provider)
        daily_counter = self._daily_counters.setdefault(daily_key, TokenCounter())
        daily_counter.input_tokens += input_tokens
        daily_counter.output_tokens += output_tokens
        current = self._estimate_daily_cost(provider, business_line_id, day)
        budget = self._budgets.get(key)
        self._emit(
            "cost.updated",
            {
                "provider": provider,
                "business_line_id": business_line_id,
                "day": day,
                "input_tokens": counter.input_tokens,
                "output_tokens": counter.output_tokens,
                "total_tokens": counter.total_tokens,
                "daily_input_tokens": daily_counter.input_tokens,
                "daily_output_tokens": daily_counter.output_tokens,
                "daily_total_tokens": daily_counter.total_tokens,
                "current": current,
                "budget": budget,
            },
        )
        if budget is not None:
            self._emit_budget_events(provider, business_line_id, day, budget, current)

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
            self._daily_counters.clear()
            self._warning_days.clear()
            return
        keys_to_delete = [
            key
            for key in self._counters
            if (provider is None or key[1] == provider)
            and (business_line_id is None or key[0] == business_line_id)
        ]
        for counter_key in keys_to_delete:
            self._counters.pop(counter_key, None)
        daily_keys_to_delete: list[tuple[str, str, str]] = [
            key
            for key in self._daily_counters
            if (provider is None or key[2] == provider)
            and (business_line_id is None or key[1] == business_line_id)
        ]
        for daily_key_to_delete in daily_keys_to_delete:
            self._daily_counters.pop(daily_key_to_delete, None)
            self._warning_days.discard(daily_key_to_delete)

    def get_daily_cost(
        self,
        provider: str,
        business_line_id: str = DEFAULT_BUSINESS_LINE_ID,
        day: date | str | None = None,
    ) -> CostBreakdown:
        """Return one daily scoped cost summary."""

        day_key = self._normalize_day(day)
        counter = self._daily_counters.get((day_key, business_line_id, provider), TokenCounter())
        return CostBreakdown(
            provider=provider,
            input_tokens=counter.input_tokens,
            output_tokens=counter.output_tokens,
            business_line_id=business_line_id,
        )

    def report_period(
        self,
        start: date | str,
        end: date | str,
        provider: str | None = None,
        business_line_id: str | None = None,
    ) -> CostBreakdown:
        """Return token usage for a date range, inclusive."""

        start_key = self._normalize_day(start)
        end_key = self._normalize_day(end)
        matching = [
            counter
            for (day, line_id, counter_provider), counter in self._daily_counters.items()
            if start_key <= day <= end_key
            and (provider is None or counter_provider == provider)
            and (business_line_id is None or line_id == business_line_id)
        ]
        return CostBreakdown(
            provider=provider or "*",
            business_line_id=business_line_id or "*",
            input_tokens=sum(item.input_tokens for item in matching),
            output_tokens=sum(item.output_tokens for item in matching),
        )

    def reset_daily(
        self,
        day: date | str | None = None,
        provider: str | None = None,
        business_line_id: str | None = None,
    ) -> None:
        """Reset daily counters for one day or scope."""

        day_key = self._normalize_day(day)
        keys_to_delete = [
            key
            for key in self._daily_counters
            if key[0] == day_key
            and (provider is None or key[2] == provider)
            and (business_line_id is None or key[1] == business_line_id)
        ]
        for key in keys_to_delete:
            self._daily_counters.pop(key, None)
            self._warning_days.discard(key)

    def _estimate_cost(self, provider: str, business_line_id: str) -> float:
        """Estimate cost until the pricing engine exists."""

        counter = self._counters.get((business_line_id, provider), TokenCounter())
        return counter.total_tokens * 0.001

    def _estimate_daily_cost(self, provider: str, business_line_id: str, day: str) -> float:
        """Estimate daily cost until the pricing engine exists."""

        counter = self._daily_counters.get((day, business_line_id, provider), TokenCounter())
        return counter.total_tokens * 0.001

    def _emit_budget_events(
        self,
        provider: str,
        business_line_id: str,
        day: str,
        budget: float,
        current: float,
    ) -> None:
        """Publish warning and exceeded budget events for the current day."""

        warning_key = (day, business_line_id, provider)
        if current >= budget * 0.8 and warning_key not in self._warning_days:
            self._warning_days.add(warning_key)
            self._emit(
                "cost.budget_warning",
                {
                    "provider": provider,
                    "business_line_id": business_line_id,
                    "day": day,
                    "budget": budget,
                    "current": current,
                    "threshold": 0.8,
                },
            )
        if current > budget:
            self._emit(
                "cost.budget_exceeded",
                {
                    "provider": provider,
                    "business_line_id": business_line_id,
                    "day": day,
                    "budget": budget,
                    "current": current,
                },
            )

    def _today(self) -> date:
        """Return the current logical day."""

        return self._today_provider()

    def _normalize_day(self, day: date | str | None) -> str:
        """Normalize date inputs to ISO strings."""

        if day is None:
            return self._today().isoformat()
        if isinstance(day, date):
            return day.isoformat()
        return day

    def _emit(self, event_type: str, payload: dict[str, object]) -> None:
        """Publish an event if an EventBus is configured."""

        if self._event_bus is not None:
            self._event_bus.emit(event_type, payload)
