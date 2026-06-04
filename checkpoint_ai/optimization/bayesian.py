"""Simple Bayesian optimization spike for bounded continuous parameters."""

from __future__ import annotations

import math

from checkpoint_ai.optimization.models import (
    OptimizationDirection,
    ParameterBounds,
    ParameterObservation,
    ParameterSuggestion,
)


class SimpleBayesianOptimizer:
    """Conservative one-dimensional optimizer with a surrogate-style score."""

    def __init__(self, grid_size: int = 25, exploration_weight: float = 0.15) -> None:
        self.grid_size = max(3, grid_size)
        self.exploration_weight = exploration_weight

    def suggest(
        self,
        scenario_id: str,
        target_id: str,
        bounds: ParameterBounds,
        observations: list[ParameterObservation],
        direction: OptimizationDirection = OptimizationDirection.MAXIMIZE,
    ) -> ParameterSuggestion:
        """Suggest the next candidate value without executing it."""

        relevant = [
            observation
            for observation in observations
            if observation.parameter_name == bounds.parameter_name
            and bounds.minimum <= observation.value <= bounds.maximum
        ]
        if len(relevant) < 2:
            midpoint = self._round_to_step((bounds.minimum + bounds.maximum) / 2, bounds)
            return ParameterSuggestion(
                scenario_id=scenario_id,
                target_id=target_id,
                parameter_name=bounds.parameter_name,
                suggested_value=midpoint,
                expected_score=0.0,
                confidence=0.0,
                reason="exploration midpoint because fewer than 2 observations exist.",
                observations_used=len(relevant),
                direction=direction,
            )

        observed_values = {round(observation.value, 10) for observation in relevant}
        best_value = relevant[0].value
        best_expected = math.inf if direction == OptimizationDirection.MINIMIZE else -math.inf
        best_acquisition = -math.inf
        for candidate in self._grid(bounds):
            if round(candidate, 10) in observed_values:
                continue
            expected = self._surrogate(candidate, relevant)
            uncertainty = self._uncertainty(candidate, relevant, bounds)
            comparable = -expected if direction == OptimizationDirection.MINIMIZE else expected
            acquisition = comparable + (uncertainty * self.exploration_weight)
            if acquisition > best_acquisition:
                best_acquisition = acquisition
                best_expected = expected
                best_value = candidate

        confidence = min(0.95, 0.35 + (len(relevant) / 20))
        return ParameterSuggestion(
            scenario_id=scenario_id,
            target_id=target_id,
            parameter_name=bounds.parameter_name,
            suggested_value=self._round_to_step(best_value, bounds),
            expected_score=round(float(best_expected), 10),
            confidence=round(confidence, 4),
            reason=f"surrogate optimum from {len(relevant)} observations.",
            observations_used=len(relevant),
            direction=direction,
        )

    def _grid(self, bounds: ParameterBounds) -> list[float]:
        if bounds.step is not None:
            values: list[float] = []
            current = bounds.minimum
            while current <= bounds.maximum + 1e-9:
                values.append(round(current, 10))
                current += bounds.step
            return values
        width = bounds.maximum - bounds.minimum
        return [
            round(bounds.minimum + (width * index / (self.grid_size - 1)), 10)
            for index in range(self.grid_size)
        ]

    @staticmethod
    def _surrogate(candidate: float, observations: list[ParameterObservation]) -> float:
        weighted_total = 0.0
        weight_sum = 0.0
        for observation in observations:
            distance = abs(candidate - observation.value)
            weight = 1.0 / (distance + 1e-6)
            weighted_total += observation.score * weight
            weight_sum += weight
        return weighted_total / weight_sum if weight_sum else 0.0

    @staticmethod
    def _uncertainty(
        candidate: float,
        observations: list[ParameterObservation],
        bounds: ParameterBounds,
    ) -> float:
        nearest = min(abs(candidate - observation.value) for observation in observations)
        width = max(bounds.maximum - bounds.minimum, 1e-9)
        return min(1.0, nearest / width)

    @staticmethod
    def _round_to_step(value: float, bounds: ParameterBounds) -> float:
        if bounds.step is None:
            return round(value, 10)
        steps = round((value - bounds.minimum) / bounds.step)
        rounded = bounds.minimum + (steps * bounds.step)
        return round(min(bounds.maximum, max(bounds.minimum, rounded)), 10)
