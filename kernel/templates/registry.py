"""Template registry."""

from __future__ import annotations

from kernel.templates.models import BusinessLineTemplate


class TemplateRegistry:
    """Register and look up BusinessLine templates."""

    def __init__(self, templates: list[BusinessLineTemplate] | None = None) -> None:
        """Create a registry with optional templates."""

        self._templates: dict[str, BusinessLineTemplate] = {}
        for template in templates or []:
            self.register(template)

    def register(self, template: BusinessLineTemplate) -> None:
        """Register or replace a template."""

        self._templates[template.id] = template

    def get(self, template_id: str) -> BusinessLineTemplate:
        """Return one template by id."""

        template = self._templates.get(template_id)
        if template is None:
            raise KeyError(f"Template not found: {template_id}")
        return template

    def list(self) -> list[BusinessLineTemplate]:
        """List templates in registration order."""

        return list(self._templates.values())
