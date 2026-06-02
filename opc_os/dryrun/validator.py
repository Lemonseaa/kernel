"""Dry run validation helpers."""

from __future__ import annotations

from dataclasses import dataclass, field

from opc_os.models import TaskSpec


@dataclass(slots=True)
class DryRunValidationResult:
    """Validation result for a dry run preview."""

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


class DryRunValidator:
    """Validate workflow inputs before a dry run."""

    def validate_task_specs(self, task_specs: list[TaskSpec]) -> DryRunValidationResult:
        """Validate task specs are executable enough for preview."""

        errors: list[str] = []
        warnings: list[str] = []
        if not task_specs:
            errors.append("At least one task is required.")
        for index, spec in enumerate(task_specs):
            if not spec.description.strip():
                errors.append(f"Task {index} description is empty.")
            if not spec.capability:
                warnings.append(f"Task {index} has no capability; simple.execute will be used.")
        return DryRunValidationResult(valid=not errors, errors=errors, warnings=warnings)
