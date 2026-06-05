# V7 Plan

## Positioning

V7 = Proposal Generation Loop.

V7 的目标不是让 CheckpointAI 进入无人值守执行，而是让系统能自动发现问题、自动提出小改、自动验证、自动记录，并把合格候选送入 Approval Inbox 或 V6 AutoActionQueue。

V7 继承 V6 边界：

- Agent 不直接执行改动
- 执行只能走 `AutoActionQueue` / adapter safe-apply
- 所有关键状态必须落 Ledger / Store / DecisionLog
- live / production / 实盘 / 发布仍由人控制

## Core Architecture

```text
BusinessLine
  -> InternalOptimizationSystem
       -> Observer Hive
       -> ObservationAggregator
       -> Proposer Hive
       -> ProposalRanker
       -> SafetyMonitor
       -> ShadowReplayScheduler
       -> Validator
       -> ConfigVersionManager
  -> ExternalAgentAdapters[]
       -> TradingAgentsAdapter
       -> ContentAgentAdapter
       -> CustomerAgentAdapter
```

协作方式：

```text
Hive Exploration + Blackboard + State Machine
```

- Hive 只负责探索和候选生成
- Blackboard 是结构化事实层，不是自由聊天上下文
- State Machine 决定下一步
- Safety / Policy / Risk 用代码做裁决
- Queue 执行，Ledger 记录

## Internal Agents

V7 正式命名：

| Agent | Role | Does | Does Not |
|---|---|---|---|
| Observer | 观察者 | 发现异常、机会、趋势 | 不生成改动 |
| Proposer | 建议者 | 生成小 patch proposal | 不执行改动 |
| Validator | 验证解释者 | 总结 shadow/replay 是否变好 | 不跑验证、不 apply |
| SafetyMonitor | 安全监控 | 阻断风险、解释回归、提出回滚建议 | 不绕过 policy |

第一版可以有多个窄职责 Observer / Proposer，但输出必须结构化。

## Blackboard Objects

V7 新增对象：

```text
Observation
Diagnosis
GeneratedProposal
ProposalCandidate
ProposalRanking
SafetyFinding
ValidationSummary
ConfigVersion
ConfigBranch
AgentConfig
ExternalAgentConnection
UserProfile
SuggestedProfileNotes
```

这些对象都必须带：

- `business_line_id`
- `scenario_id`
- `source_ids`
- `created_at`
- `metadata`

## Dynamic Balance

动态平衡不靠 Agent 自觉，靠控制结构：

| Mechanism | Purpose | Owner |
|---|---|---|
| Guardrails | 防越界 | code + SafetyMonitor explanation |
| Cooldown | 防震荡 | code |
| Diversity | 防局部最优 | Proposer Hive + Ranker |
| Regression Detection | 防负向优化 | code + SafetyMonitor explanation |
| Budget Control | 防成本失控 | code |
| Conflict Detection | 防多改互相污染 | code |
| Version Branching | 保留好配置，允许继续优化或重开分支 | UI + ConfigVersionManager |

## External Agent Contract

外置 Agent 必须通过 adapter 契约接入：

```text
run_task(input) -> ExternalRunResult
run_shadow(change, input) -> ExternalRunResult
get_metrics(run_id) -> MetricSet
get_trace(run_id) -> Trace
apply_change(change, checkpoint_id) -> ApplyResult
rollback(checkpoint_id) -> RollbackResult
list_config() -> ExternalConfig
```

第一版只需要 `run_task` / `run_shadow` / `get_metrics` / `get_trace`，不急着实现真实 `apply_change`。

## V7 Version Breakdown

### V7.1: Blackboard + Contracts

目标：建立 V7 数据模型、stores、状态机骨架。

验收：

- `ObservationStore` 可保存/查询 observation
- `SafetyFindingStore` 可保存/查询 safety finding
- `ValidationSummaryStore` 可保存/查询 validation summary
- 所有对象强制 business_line / scenario scope
- Loop state 不依赖 Agent 自由对话

### V7.2: Observer Hive

目标：系统能从 runs / metrics / decision logs / cost / data quality 中自动发现问题或机会。

验收：

- 至少两个 Observer：MetricObserver、DecisionObserver
- Observer 输出结构化 `Observation`
- Aggregator 去重、排序、过滤噪音
- 同一轮最多输出 top N observation

### V7.3: Proposer Hive + Ranking

目标：系统能从 observation 自动生成小改 proposal，并选出最值得验证的候选。

验收：

- 至少两个 Proposer：PromptProposer、ParameterProposer
- 只能生成 patch，不允许全文重写
- ProposalRanker 按小改、低风险、可验证、历史成功率排序
- ConflictDetector 默认同一 target 一轮只允许一个 proposal

### V7.4: Shadow/Replay Scheduler + Validator

目标：proposal 自动进入 shadow/replay 验证，Validator 生成可读结论。

验收：

- ShadowReplayScheduler 不 apply，只调 adapter shadow/replay
- Validator 输出 `ValidationSummary`
- 结果回答：变好了什么、变差了什么、是否建议入审批/队列
- synthetic 结果不能进入 auto queue

### V7.5: SafetyMonitor + Dynamic Balance

目标：把 guardrails、cooldown、diversity、regression、budget、conflict 变成可测试规则。

验收：

- Guardrail violation 阻断 proposal
- Cooldown 阻止同 target 高频改动
- Budget limit 阻止过度探索
- Regression detection 可生成 rollback suggestion
- SafetyFinding 可进入 report / UI

### V7.6: Config Versioning + Branching

目标：人看到效果好时，可以锁定配置；之后可继续在该分支优化，也可从锁定版本开新分支。

验收：

- ConfigVersion 可保存完整配置快照
- Lock 后当前版本只读
- Branch 可基于 locked version 创建新优化分支
- Switch 可切换 active branch
- Rollback 可回到 locked version
- UI 有独立按钮，不依赖 Hermes

### V7.7: Agent Config + External Adapter Management

目标：每条业务线能独立配置内置 Agent 技能、工具、MCP server、触发条件、约束和模型；可管理多个外置 Agent adapter；Agent context 只能读取人类确认过的正式偏好。

验收：

- AgentConfig 按 business_line + role + config_version 隔离
- UI 弹窗可查看/编辑 skills、tools、mcp_servers、triggers、constraints、model
- Hermes 只能解释配置，不是唯一配置入口
- ExternalAgentConnection 可绑定多个外置系统到一条业务线
- `user/USER_PROFILE.md` 是正式偏好唯一来源
- `user/SUGGESTED_PROFILE_NOTES.md` 只作为 Hermes 草稿，不作为正式约束
- Hermes 不可直接修改正式 profile

### V7.8: V7 Stable

目标：端到端证明系统能自动发现、自动提案、自动验证、自动记录，但不失控。

验收：

- 一条业务线至少跑 20 次真实或半真实 run
- 系统自动生成至少 5 个 observation
- 系统自动生成至少 3 个 proposal
- 至少 2 个 proposal 自动跑 shadow/replay
- 至少 1 个 proposal 进入 Approval Inbox
- 0 个未授权真实 apply
- 报告能回答：发现了什么、为什么改、改了什么、验证结果、是否变好、是否阻断

## Non-Goals

- 不做 Agent 自由聊天系统
- 不把 CrewAI 作为核心依赖
- 不做外部 AI 直接访问数据库
- 不做自动实盘
- 不做自动发布
- 不做 prompt 全文重写器
- 不做复杂企业权限
- 不做插件市场

## Implementation Rule

每个阶段必须先有数据模型和测试，再写实现。

每个阶段必须能回答：

1. 输入是什么
2. 输出是什么
3. 谁可以阻断
4. 是否落库
5. 是否可回滚
6. 是否跨业务线污染
