# Kernel

Agent Workflow Kernel for building a general multi-agent operating system.

This repository starts with the core runtime skeleton and will grow around real workflow needs from OPC.

## V0.1 Scope

The first kernel version focuses on a small executable workflow core:

- Run model
- Task model and state machine
- Agent model and registry
- Workflow engine and executor
- Tool registry and permission checks
- Policy engine and human approval gate
- SQLite persistence for Run/Task state
- Event bus and audit log

## Validate Imports

```bash
python -c "from kernel.models import Run, Task, Agent; print('models OK')"
python -c "from kernel.runtime import AgentRegistry; print('runtime OK')"
python -c "from kernel.workflow import WorkflowEngine; print('workflow OK')"
python -c "from kernel.tools import ToolRegistry; print('tools OK')"
python -c "from kernel.control import PolicyEngine, HumanApprovalGate; print('control OK')"
python -c "from kernel.events import EventBus; print('events OK')"
python -c "from kernel import Kernel; print('kernel OK')"
```

## Run Tests

```bash
python -m unittest discover -s tests -v
```

## Evaluation Gate

Tasks can opt into generated-content quality checks:

```python
TaskSpec(
    description="生成小红书内容",
    evaluation_required=True,
    evaluation_platform="xiaohongshu",
    min_score=70.0,
)
```

The default gate runs readability, SEO, and platform-fit evaluators. A failing gate marks the task as
`evaluation_failed` and records suggestions in `task.result`.

## Notifications

The kernel includes a notification manager with console, webhook, and email channels. Human approval
requests can trigger notifications through the manager.

```bash
python -m kernel.cli notify --title "需要审批" --body "有任务等待处理"
```
