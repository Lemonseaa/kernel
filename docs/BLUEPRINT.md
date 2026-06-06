# CheckpointAI Blueprint

**Workflow Optimization Console**

## One Line

CheckpointAI 是一个工作流优化框架。

它不替代外部工作流，不做低代码拖拽 Builder。它接入外部 Agent / 自动化 / 业务流程，把黑盒工作流变成可观察、可比较、可验证、可持续优化的系统。

---

## Product Positioning

```text
Dify = 原型工具 / 插件生态参考 / 简单工作流可视化
TradingAgents = 量化 Agent 团队模板 / 多角色投研流程参考
CheckpointAI = 工作流观察层 + 优化层 + 审批层 + 证据层
```

CheckpointAI 的承诺：

```text
只要一个工作流愿意暴露结构、trace、metrics 和可调配置，
CheckpointAI 就能让它可观察、可比较、可回滚、可迭代优化。
```

不承诺：

```text
1. 不承诺黑盒工作流一定能被优化
2. 不承诺 synthetic / historical 结果等于真实业务成功
3. 不自动实盘、不自动发布、不绕过人类最终决策
4. 不做拖拽式 Workflow Builder
5. 不直接编辑外部项目代码作为常规能力
```

---

## Core Question

每次系统提出一个改动时，必须回答：

```text
1. 为什么要动？
2. 动了什么？
3. 改之前是什么表现？
4. 改之后是什么表现？
5. 是否比 baseline 好？
6. 是否违反风险边界？
7. 是否符合人的方法论和审美？
8. 能不能回滚？
```

如果回答不了，就不能自动优化。

---

## Architecture

```text
External Workflow / Workflow Draft
  -> Workflow Contract
  -> Workflow Map
  -> Trace / Lineage / Metrics
  -> Observation / Diagnosis
  -> Proposal Patch
  -> Policy / Risk / Methodology Check
  -> Shadow / Replay
  -> Baseline Compare
  -> Impact Visualization
  -> Approval / Lock / Rollback
```

---

## Core Modules

| Module | Purpose |
|---|---|
| Workflow Design Assistant | 用自然语言 + 表单生成可观察工作流草图，不做拖拽 Builder |
| Workflow Contract | 把外部工作流或草图转成 `WorkflowManifest` |
| Workflow Map | 可视化 stage / node / edge / run trace / 黑盒节点 |
| Trace & Lineage | 记录节点输入输出、成本、耗时、错误、配置版本 |
| Experiment Ledger | 记录假设、baseline、改动、结果和结论 |
| Optimization Engine | observation -> proposal -> shadow/replay -> validation |
| Policy & Risk | 决定自动、审批、阻断 |
| Methodology Profile | 记录人的审美、偏好、方法论和禁忌 |
| Impact Visualization | 用图表看改动后有没有变好 |
| Governance Console | 审批、决策日志、备份、回滚、Provider健康 |

---

## Workflow Design Assistant

设计入口不是自由画布，而是结构化表单：

```text
Intent Table
  -> Methodology Form
  -> Stage Map
  -> Pattern Recommendation
  -> Workflow Draft
  -> WorkflowManifest
  -> Graph Preview
```

用户填写：

```text
目标 / 输入 / 输出 / 阶段 / 风险点 / 指标 / 人工确认点 / 方法论偏好
```

系统输出：

```text
WorkflowDraft / WorkflowManifest / AgentConfigDraft / MetricSchemaDraft / PolicyDraft
```

协作模式不是全局选择，而是每个 stage 局部推荐。例如：

```text
调研阶段：Parallel Exploration / Specialist Panel
判断阶段：Critic-Refine / Debate / Voting
优化阶段：Champion-Challenger / Shadow Replay
发布阶段：Human Gate / Policy Gate
异常阶段：Fallback / Retry / Safety Monitor
```

---

## Methodology Profile

人的偏好、审美、风险边界和方法论必须由人确认。

Hermes 可以基于历史帮助总结草稿，但不能自动写入正式 profile。

规则：

```text
1. 人类填写和确认
2. Hermes 只生成建议草稿
3. Agent 不能自动修改正式方法论
4. 每次修改必须有 diff 和 DecisionLog
5. Proposal 必须显示是否符合 Methodology Profile
```

例子：

```text
量化：稳健优先还是进攻优先？能接受多大回撤？是否反感过拟合？
内容：克制表达还是强钩子？能不能标题党？审美边界在哪里？
研究：保守结论还是大胆假设？证据强度要求多高？
```

---

## Current Status

| Version | Status | Meaning |
|---|---|---|
| V1 | Done | Ledger / Feedback / Risk / Loop 基础能力 |
| V2 | Done | Scenario -> Adapter -> Logs -> Proposal -> Policy -> Shadow -> Compare |
| V3 | Done | Evidence Evaluation / MetricSchema / Recommendation / BO Spike |
| V4 | Done | Scenario隔离 / Adapter能力契约 / Compatibility / Cross-scenario preview |
| V5 | Done | Web Console / Approval / Reports / Shadows / Backup / Real Data Drill |
| V6 | Done | 低风险自治控制层：queue / audit-only / operator feedback |
| V7 | Done | Observer / Proposer / Validator / SafetyMonitor 生成闭环 |
| V7.9 | Planned | Workflow Map / Impact Charts / LLM Provider Console / Methodology UI |

---

## V7.9 Priority

V7.9 不新增更聪明的 Agent，而是补判断界面和透明层。

必须做：

```text
1. Workflow Contract + Workflow Map
2. Run Trace 可视化
3. 黑盒节点 / 低透明度节点标记
4. Impact Charts：before/after、trend、baseline/candidate、proposal质量
5. LLM Provider Console：provider、model、role routing、health、cost
6. Methodology Profile UI：人填、人确认、Hermes只辅助总结
7. 至少 30-50 条 demo / historical / semi-real run 做 burn-in
```

V7.9 验收：

```text
1. 人能看懂一个工作流怎么跑
2. 人能看出哪里是黑盒
3. 人能看出一次改动有没有变好
4. 人能看出建议是否符合自己的方法论
5. 人能看出哪个模型在什么角色上花了多少钱、稳不稳定
6. 报告能指出：黑盒节点、指标盲区、方法论冲突和下一步修复建议
```

---

## Data Principle

不要靠想象推进版本。

每进入下一阶段前，至少要用真实或半真实数据跑一轮：

```text
1. synthetic 只能验证结构
2. historical 可以验证评估和对比
3. paper / shadow 可以验证策略稳定性
4. live / production 只能由人决定部署
```

如果数据暴露结构问题，先修结构，不急着进下一版本。

---

## Boundaries

| Area | Rule |
|---|---|
| Prompt | 默认 patch-first，不全文重写；大改走 refactor proposal |
| Policy | Policy 在 shadow 前，BLOCKED 不消耗 shadow 资源 |
| Shadow | 不污染 live prompt / live config |
| Scenario | 默认隔离，跨 scenario 必须显式开启 |
| Data | business / system / data quality metrics 必须分开 |
| Human | 人类保留发布、实盘、删除、正式方法论确认权 |
| Hermes | 能解释、总结、起草；不能越权确认 |

---

## Document Map

保留少量源头文档，避免重复规划。

| Document | Role |
|---|---|
| `docs/BLUEPRINT.md` | 总纲，唯一产品方向源头 |
| `docs/WEB_UI_PLAN.md` | Web UI / Console 详细计划 |
| `docs/V7_PLAN.md` | V7 Agent生成闭环执行计划 |
| `docs/USER_PREFERENCE_PLAN.md` | 用户偏好和 Hermes 草稿机制 |
| `docs/metrics_reference.md` | 指标定义参考 |
| `docs/adapter_checklist.md` | Adapter 接入评估清单 |
| `docs/deployment/` | 部署与运维 |

历史文档和报告只作为审计记录，不作为路线图来源。

---

## Next Step

当前下一步：

```text
V7.9 Phase 1: Workflow Contract + Workflow Map
```

先做能让人看清工作流结构和黑盒位置的能力，再做更多自动优化。
