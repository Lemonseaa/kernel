# checkpointAI

[![Tests](https://img.shields.io/badge/tests-112%20passed-brightgreen)](https://github.com/Lemonseaa/checkpointAI)
[![Python](https://img.shields.io/badge/python-3.11+-blue)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/docker-ready-blue)](https://www.docker.com/)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

checkpointAI — 多Agent操作系统的核心运行时。

checkpointAI is an Agent Workflow checkpointAI for building a general multi-agent operating system.

## 核心特性

- **Human-in-the-Loop** — AI执行，你做决策
- **Evaluation Gate** — 内容质量自动评估
- **成本控制** — 实时追踪，超预算自动停
- **6层安全机制** — Policy/Tool/HumanGate/Cost/Event/KillSwitch
- **BusinessLine隔离** — 多业务线完全独立
- **HA支持** — 主备自动切换

## 快速开始

```bash
# 1. 安装
pip install -e .

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 填入你的 API Key

# 3. 运行
checkpointai status

# 4. 创建业务线
checkpointai bl create --name "内容业务" --template content
```

或者用Docker：

```bash
# 1. 配置
cp .env.example .env

# 2. 启动
docker compose up -d

# 3. 检查状态
docker compose ps
```

## 核心概念

### Python API

系统入口，管理所有组件。

```python
from checkpoint_ai import CheckpointAI

k = CheckpointAI()
bl = k.create_business_line('my_business', template='content')
run = k.create_run(bl.id, '写一篇关于AI的文章')
```

### BusinessLine

业务线隔离，每个业务线有独立的Agent、Context、Cost。

```python
# 创建业务线
bl = k.create_business_line('课程业务', template='content')

# 业务线之间完全隔离
context_a = k.memory.get_context(business_line_id=a.id)
context_b = k.memory.get_context(business_line_id=b.id)
# context_a 和 context_b 互不影响
```

### Agent

LLM驱动的执行单元。

```python
agent = k.register_agent(
    name='writer',
    model='minimax',
    system_prompt='你是一个专业的内容写手'
)
```

### Run / Task

Run是执行上下文，Task是具体任务。

```python
run = k.create_run(bl.id, '生成内容')
task = k.create_task(run.id, '写小红书文章')
```

### Evaluation Gate

内容质量自动评估，不达标打回重写。

```python
TaskSpec(
    description='生成小红书内容',
    evaluation_required=True,
    evaluation_platform='xiaohongshu',
    min_score=70.0,
)
```

### Policy

6层安全机制。

```python
# PolicyEngine 自动拦截高风险操作
PolicyRule(
    name='block_dangerous_tools',
    scope='GLOBAL',
    action='DENY',
    tool_names=['rm', 'sudo']
)
```

### Human Gate

审批流程，AI执行你确认。

```python
# 发布类操作需要审批
HumanApprovalRequest(
    task_id=task.id,
    reason='文章即将发布到小红书',
    requested_by='writer_agent'
)
```

### Cost Tracker

成本实时追踪。

```python
# 设置每日预算
k.cost_tracker.set_daily_budget('minimax', 100.0)

# 超预算自动停
# 超80%告警，95%critical，100%停
```

### Event Bus

统一事件流。

```python
# 所有操作都有记录
k.event_bus.subscribe('task.completed', my_handler)
```

## 架构图

```
┌─────────────────────────────────────────────────────┐
│                     CheckpointAI                          │
├─────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐            │
│  │ Business│  │  Agent  │  │  Run/   │            │
│  │  Line   │  │Registry │  │  Task   │            │
│  └────┬────┘  └────┬────┘  └────┬────┘            │
│       │             │             │                  │
│  ┌────▼────┐  ┌────▼────┐  ┌────▼────┐            │
│  │ Context │  │ LLM     │  │Workflow │            │
│  │ Manager │  │Provider │  │ Engine  │            │
│  └────┬────┘  └────┬────┘  └────┬────┘            │
│       │             │             │                  │
│  ┌────▼─────────────▼─────────────▼────┐            │
│  │              Event Bus              │            │
│  └────┬─────────────┬─────────────┬────┘            │
│       │             │             │                  │
│  ┌────▼────┐  ┌────▼────┐  ┌────▼────┐  ┌─────┐  │
│  │Evaluation│  │ Policy  │  │ Human   │  │Cost │  │
│  │  Gate   │  │ Engine  │  │  Gate   │  │Track│  │
│  └─────────┘  └─────────┘  └─────────┘  └─────┘  │
│                                                     │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐            │
│  │Notifier │  │  Alert  │  │Health   │            │
│  │Manager │  │ Manager │  │ Checker │            │
│  └─────────┘  └─────────┘  └─────────┘            │
└─────────────────────────────────────────────────────┘
```

## 模块说明

| 模块 | 说明 |
|---|---|
| checkpoint_ai/agent/ | Agent定义和LLM集成 |
| checkpoint_ai/businessline/ | 业务线隔离 |
| checkpoint_ai/cache/ | LLM响应缓存 |
| checkpoint_ai/context/ | Context管理和持久化 |
| checkpoint_ai/control/ | Policy和HumanGate |
| checkpoint_ai/diagnostics/ | 健康检查和告警 |
| checkpoint_ai/evaluation/ | Evaluation Gate |
| checkpoint_ai/events/ | Event Bus |
| checkpoint_ai/llm/ | LLM Provider抽象 |
| checkpoint_ai/memory/ | 记忆系统 |
| checkpoint_ai/notification/ | 通知系统 |
| checkpoint_ai/observability/ | Cost追踪和指标 |
| checkpoint_ai/plugins/ | 插件注册表 |
| checkpoint_ai/runtime/ | Agent运行时 |
| checkpoint_ai/scheduler/ | 定时任务 |
| checkpoint_ai/storage/ | SQLite持久化 |
| checkpoint_ai/tools/ | 工具注册和权限 |
| checkpoint_ai/webhook/ | Webhook发送和接收 |
| checkpoint_ai/ha/ | 高可用 |

## 脚本

```bash
# 开发测试
python -m unittest discover -s tests -v

# 性能基准
python scripts/benchmark.py --runs 20

# 压力测试
python scripts/stress_test.py --runs 50 --concurrency 5

# 安全审计
python scripts/security_audit.py

# 健康检查
python scripts/health_check.py

# 最终验收
python scripts/final_acceptance.py

# CLI
checkpointai status
checkpointai run list
checkpointai bl list
checkpointai health
```

## Docker部署

```bash
# 启动
docker compose up -d

# HA模式（需要2个实例）
docker compose --profile ha up -d

# 查看日志
docker compose logs -f

# 进入容器
docker compose exec checkpoint_ai bash
```

详见 [docs/deployment](docs/deployment/README.md)

## 许可证

MIT License — 详见 [LICENSE](LICENSE)

## GitHub

https://github.com/Lemonseaa/checkpointAI
