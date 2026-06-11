# CheckpointAI Strategic Reset Plan

## Why Reset

CheckpointAI 过去 V1-V7 证明了很多能力，也暴露了一个问题：继续做通用 Agent 平台、Workflow Engine、插件生态、模型操作台，会和成熟项目重复。

新的方向不是推倒重来，而是收缩：

```text
CheckpointAI = External Workflow Evidence Harness
```

也就是给外部工作流加一层证据、可视化诊断、验证、审批和回滚能力。

---

## New Positioning

CheckpointAI 不再定位为：

```text
Multi-Agent OS
Workflow Runtime
Agent Platform
Low-code Builder
Plugin Marketplace
TradingAgents / Dify / Nexent 替代品
```

CheckpointAI 只做：

```text
External Workflow
  -> Evidence Adapter
  -> Workflow Contract
  -> Workflow Visualization
  -> Trace + Metrics
  -> Baseline Compare
  -> Evidence Review
  -> Approval / Reject / Rollback
```

核心问题：

```text
这个外部工作流到底怎么跑？
哪里是黑盒？
这个外部工作流改了以后，到底有没有变好？
证据够不够？
风险有没有变大？
人该不该批准？
```

---

## What We Stop Building

以下方向冻结，不继续补完：

| Area | Decision |
|---|---|
| Generic Agent Runtime | stop |
| Message Bus / Registry / Scheduler as platform | stop |
| Full Workflow Engine | stop |
| Drag-and-drop Workflow Builder | stop |
| Plugin Marketplace | stop |
| Full LLM Provider Platform | stop |
| HA / Kubernetes Enterprise Platform | stop |
| TradingAgents Clone | stop |
| Dify / Nexent Clone | stop |
| Cross-scenario learning automation | pause |
| Auto live trading / auto publishing | blocked |

这些模块已有代码不立刻删除。先标记 legacy / frozen，等新 Evidence path 跑通后按引用关系清理。

---

## What We Keep

这些是 CheckpointAI 的核心，不是重复造轮子：

| Module | Why Keep |
|---|---|
| Evidence Adapter | 外部工作流接入入口 |
| Workflow Contract | 标准化 workflow structure / trace / metrics / config |
| Workflow Visualization | 让人看清结构、路径、黑盒、覆盖率、风险和成本 |
| Experiment Ledger | 记录假设、baseline、改动、结果、结论 |
| Metric Schema | 指标有方向、权重、类别，避免裸 diff |
| Baseline Compare | 判断 candidate 是否真的更好 |
| Shadow / Replay | 候选改动不直接污染 live |
| Decision Log | 沉淀 approve / reject / rollback 原因 |
| Policy / Risk Gate | 控制自动、审批、阻断 |
| Approval Inbox | 人类集中处理高价值决策 |
| Backup / Rollback | 允许安全恢复 |
| Reports | 把证据变成人能判断的报告 |
| Methodology Profile | 人的方法论、审美、风险偏好进入判断 |

---

## Phase R1: Evidence Adapter + Workflow Visualization

目标：先不接复杂系统，定义一个统一的外部工作流运行结果输入格式，并把接入后的工作流画成诊断图。

Workflow Visualization 不是拖拽式 builder。它是诊断图，用来回答：

```text
1. 工作流有哪些节点？
2. 本次 run 实际走了哪些路径？
3. 哪些节点是黑盒？
4. 哪些节点有 trace？
5. 哪些节点有 metric？
6. 哪些节点可 replay？
7. 哪些节点成本高、延迟高、失败多？
```

### Input Contract

```json
{
  "workflow_id": "quant_backtest_v1",
  "run_id": "run_001",
  "run_kind": "historical",
  "started_at": "2026-06-11T10:00:00Z",
  "finished_at": "2026-06-11T10:03:00Z",
  "nodes": [],
  "edges": [],
  "trace": [],
  "metrics": {},
  "metric_schema": {},
  "config": {},
  "artifacts": [],
  "metadata": {}
}
```

### Required Output

```text
Workflow Contract
Workflow Visualization Data
Trace Summary
Metric Summary
Trace Coverage
Metric Coverage
Black-box Node List
Baseline Comparison
Evidence Report
Decision Recommendation
```

### Acceptance

```text
1. Can ingest one external workflow run JSON
2. Can normalize nodes / edges / trace / metrics
3. Can build workflow map data from nodes / edges / trace
4. Can mark black-box nodes
5. Can calculate trace coverage and metric coverage
6. Can classify metrics: business / system / data_quality
7. Can compare against baseline
8. Can generate an evidence report
9. Can store the run and report in existing stores
```

---

## Phase R2: Quant Backtest Drill

目标：用真实或半真实量化回测数据验证 Evidence Loop。

最小场景：

```text
baseline strategy
candidate strategy
same market universe
same historical period
same transaction cost assumptions
```

必须记录：

```text
return
sharpe
max_drawdown
win_rate
trade_count
turnover
latency / runtime
data_quality
```

必须回答：

```text
1. 改了什么参数或策略？
2. 收益是否提高？
3. 回撤是否变差？
4. 样本是否足够？
5. 是否可能过拟合？
6. 是否建议进入模拟盘？
```

验收：

```text
1. 至少 30 次 historical / semi-real backtest run
2. 至少 5 个 candidate vs baseline comparison
3. 至少 3 份 evidence report
4. 至少 1 次 approve / reject decision
5. 至少 1 张 workflow visualization 能展示 run path、black-box node、coverage
6. 发现并记录至少 3 个系统问题或指标盲区
```

---

## Phase R3: Evidence Review

目标：借鉴 ARIS 的对抗审思路，把 CheckpointAI 从“记录系统”升级为“可信判断系统”。

新增审查层：

| Review | Question |
|---|---|
| Metric Audit | 指标计算是否可信？ |
| Claim Audit | 结论是否由指标支持？ |
| Baseline Audit | baseline 是否公平？ |
| Risk Audit | 风险是否被低估？ |
| Human Checkpoint | 是否需要人类确认？ |

验收：

```text
1. Evidence report includes audit section
2. Weak evidence is marked as inconclusive
3. Validator can disagree with proposer
4. Human sees why a result is not trustworthy
```

---

## Phase R4: Impact Console

目标：只做 Evidence path 必需 UI，不扩展成平台。

必须有：

```text
Run list
Run detail
Workflow visualization
Baseline vs Candidate
Metric trend
Evidence report
Approval decision
Rollback / backup entry
```

暂不做：

```text
Drag builder
Agent marketplace
Complex provider console
Cross-scenario insight automation
Workflow generation assistant
```

---

## Code Cleanup Rule

不要一开始大删代码。

顺序：

```text
1. Freeze old platform directions
2. Build Evidence Adapter
3. Run Quant Backtest Drill
4. Mark unused legacy modules
5. Delete only after new path has tests and data
```

删除标准：

```text
1. Not referenced by Evidence Adapter path
2. Not used by tests
3. Only serves old Multi-Agent OS direction
4. Duplicates mature external tools
```

---

## Tool Strategy

| Tool / Project | How to Use |
|---|---|
| Archon | 借鉴 YAML workflow contract / approval gate，不复刻 engine |
| ARIS | 借鉴 adversarial review / evidence audit |
| learn-harness-engineering | 当作设计原则，不当依赖 |
| Nexent | 作为未来可接入外部 agent 平台，不竞争 |
| Dify | 原型和插件参考，不替代 |
| TradingAgents | 量化工作流样板和数据来源，不复刻 |
| LiteLLM / OpenRouter | 模型适配可借用，不自建完整 provider 平台 |

---

## Immediate Next Step

下一步只做一件事：

```text
Implement External Workflow Evidence Adapter + Workflow Visualization data model
```

不是 V8，不是新平台，不是更多 UI。

第一轮交付：

```text
checkpointai evidence ingest sample_quant_run.json
checkpointai evidence visualize --run run_a
checkpointai evidence compare --baseline run_a --candidate run_b
checkpointai evidence report --run run_b
```

如果这个闭环不能让人判断“改动有没有变好”，就先修 Evidence path，不继续扩展其他功能。
