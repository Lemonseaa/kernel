"""Apply templates to BusinessLines."""

from __future__ import annotations

from opc_os.businessline import BusinessLine, BusinessLineConfig
from opc_os.templates.models import BusinessLineTemplate


class TemplateApplier:
    """Convert templates into BusinessLine configuration."""

    def apply(self, name: str, template: BusinessLineTemplate) -> BusinessLine:
        """Create an unsaved BusinessLine from a template."""

        config = BusinessLineConfig(
            evaluation_rules=list(template.evaluation_rules),
            agent_templates=[agent.id for agent in template.agents],
            workflow_templates=[workflow.id for workflow in template.workflows],
            policy_ids=list(template.policy_ids),
        )
        return BusinessLine(name=name, config=config)
