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
