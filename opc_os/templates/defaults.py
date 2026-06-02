"""Built-in BusinessLine templates."""

from __future__ import annotations

from opc_os.templates.models import AgentTemplate, BusinessLineTemplate, WorkflowTemplate


def builtin_templates() -> list[BusinessLineTemplate]:
    """Return built-in templates for zero-configuration setup."""

    return [
        BusinessLineTemplate(id="blank", name="空白业务线"),
        BusinessLineTemplate(
            id="content",
            name="内容业务",
            description="OPC content creation workflow defaults.",
            agents=[
                AgentTemplate(
                    id="content.researcher",
                    name="researcher",
                    role="选题研究",
                    capabilities=["content.research"],
                ),
                AgentTemplate(
                    id="content.writer",
                    name="writer",
                    role="内容写作",
                    capabilities=["content.write"],
                ),
                AgentTemplate(
                    id="content.editor",
                    name="editor",
                    role="内容审核",
                    capabilities=["content.edit"],
                ),
            ],
            workflows=[
                WorkflowTemplate(
                    id="content.default_flow",
                    name="默认内容工作流",
                    task_descriptions=["选题", "规划", "写作", "审核", "分发"],
                )
            ],
            evaluation_rules=["readability", "seo_quality", "platform_adapter", "originality"],
            policy_ids=["publish_require_approval"],
        ),
        BusinessLineTemplate(
            id="website",
            name="网站业务",
            description="Website delivery workflow defaults.",
            agents=[
                AgentTemplate(
                    id="website.developer",
                    name="developer",
                    role="开发",
                    capabilities=["website.build"],
                ),
                AgentTemplate(
                    id="website.reviewer",
                    name="reviewer",
                    role="审核",
                    capabilities=["website.review"],
                ),
            ],
            workflows=[
                WorkflowTemplate(
                    id="website.default_flow",
                    name="默认网站工作流",
                    task_descriptions=["设计", "开发", "审核", "发布"],
                )
            ],
            evaluation_rules=["website_quality"],
            policy_ids=["deploy_require_approval"],
        ),
    ]
