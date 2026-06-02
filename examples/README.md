# Examples

实用示例，帮你快速上手 OPC-OS。

## 快速开始

**quickstart.py** — 创建业务线并运行任务

```bash
python examples/quickstart.py
```

学习内容：
- 初始化 OPC-OS
- 创建 BusinessLine
- 运行 Task

## 业务线隔离

**businessline_isolation.py** — 验证多业务线数据隔离

```bash
python examples/businessline_isolation.py
```

学习内容：
- 创建多个 BusinessLine
- 验证数据隔离
- 理解业务线边界

## 成本控制

**cost_control.py** — 设置预算并追踪开销

```bash
python examples/cost_control.py
```

学习内容：
- 设置每日预算
- 追踪 Token 消耗
- 理解成本事件

## Human Gate

**human_gate.py** — 审批流程示例

```bash
python examples/human_gate.py
```

学习内容：
- 创建 ApprovalGate
- 理解审批请求
- 掌握审批流程

## Evaluation Gate

**evaluation_gate_workflow.py** — 内容质量评估

```bash
python examples/evaluation_gate_workflow.py
```

学习内容：
- 配置 Evaluation Gate
- 设置质量阈值
- 理解评估流程

## 下一步

- 查看 [docs/ARCHITECTURE_OVERVIEW.md](../docs/ARCHITECTURE_OVERVIEW.md) 深入理解架构
- 查看 [docs/deployment](../docs/deployment/README.md) 了解部署方式
