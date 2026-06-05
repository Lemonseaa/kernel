# CheckpointAI Blueprint

## Summary

| 阶段 | 当前状态 | 核心验收 |
|---|---|---|
| V1 | 已完成 | Kernel / Ledger / Feedback / Risk / Loop 基础能力可用 |
| V2 | 已完成 | Scenario -> Adapter -> Logs -> Proposal -> Policy -> Shadow -> Compare 跑通 |
| V3 | 已完成到 V3.4 | Evidence Evaluation、MetricSchema、Recommendation、BO Spike 可用 |
| V4 | 已完成到 V4.5 | Scenario 隔离、Adapter 能力契约、Compatibility、Cross-scenario preview 可用 |
| V5 | 已完成到 V5.15 | Web Console、Approval、Reports、Shadows、Backup、Real Data Drill 可用 |
| V6 | 收口中 | 低风险自治控制层：queue、audit-only process、operator feedback |

快速导航：

- 项目边界：看“定位 / 边界 / 能力边界”
- 当前代码映射：看“当前进度”
- V5 控制台状态：看“V5 主线”
- 进入 V6 前风险：看“V5 后风险审查”
- 下一阶段规划：看“V6 主线”

---

## 定位

**CheckpointAI 是代码化的 Agent 实验与优化系统，不是低代码 Workflow Builder。**

```
Dify = 原型工具 / 工作流参考 / 插件生态参考
TradingAgents = 量化 Agent 团队模板 / 多角色投研流程参考
CheckpointAI = 实验账本 / 评估 / Baseline对比 / Shadow对比 / Patch / 版本 / 风险门控 / 审批台

CheckpointAI 不做 Dify 的低代码节点系统，但会吸收 Dify 插件生态和 TradingAgents 团队结构的有效部分。
```

---

## 核心目标

```
能不能让我每次改 Agent / 工作流都知道有没有变好？
如果这个成立，CheckpointAI 就有根了。
```

---

## 架构关系

```
Business Team Run
  -> 记录 agent trace / 工具调用 / 参数 / 输出 / 指标
  -> 生成 prompt / workflow / tool policy / strategy patch
  -> Shadow / Replay 测试
  -> 对比 baseline
  -> 风险分级
  -> 自动应用低风险改动，其他进入审批台
```

---

## 边界

| 项目 | 定位 |
|---|---|
| CheckpointAI | 主线，代码化实验与优化控制系统 |
| Dify | 原型工具，不作为最终执行层依赖 |
| Dify 插件生态 | 工具目录和封装参考，不整包搬运 |
| TradingAgents | 量化团队模板，保留多角色投研流程，接入 trace/config/replay |
| opc_agent | demo business line，可删除、可重建 |

---

## 闭环

```
Agent run -> Logs -> Evaluation -> PromptProposal -> Policy -> Shadow
          -> Baseline compare -> Approve / auto-apply low risk -> PromptVersionStore
```

```
BLOCKED: stop, no shadow
AUTO / APPROVAL: must shadow first
shadow failed: reject
shadow passed: AUTO applies, APPROVAL waits for human
```

---

## Dify 的位置

Dify 适合原型，不适合作为最终高效率系统。

```
用 Dify 做：
- 快速验证工作流
- 观察哪些节点/工具/提示词结构有价值
- 参考插件生态和工具 schema

不用 Dify 做：
- 最终复杂状态管理
- 动态循环
- 回测/计算/仿真
- 长期实验账本
- 严格测试和版本回滚
- 高可靠生产控制
```

Dify 插件生态的利用方式：

```
不把插件整包搬进 CheckpointAI
只评估插件解决什么问题、什么时候用、怎么封装、什么时候不用
有业务价值的工具，最终在代码里用 Tool Adapter / Service API 接入
```

## TradingAgents 的位置

TradingAgents 的价值是量化团队模板，不是 CheckpointAI 的替代品。

```
TradingAgents 负责：
- 多角色投研流程
- Market / News / Social / Fundamentals Analyst
- Bull / Bear Debate
- Risk Manager / Portfolio Manager
- 生成策略假设和研究报告

CheckpointAI 负责：
- 记录每个 agent 的 trace
- 评估每个角色贡献
- 管理 prompt / workflow / tool policy / strategy 版本
- Shadow / Replay 对比新版和旧版
- 判断策略能否进入回测、模拟盘、小资金实盘
```

要让 CheckpointAI 真正改善 TradingAgents，不能只看入口和出口，必须让 TradingAgents 暴露四个接口：

```
run(input, config_version) -> result
get_trace(run_id) -> traces
get_config(version) -> config
apply_config_patch(patch) -> new_config_version
```

可优化对象：

```
Prompt
Workflow structure
Tool policy
Decision rule
Risk gate
Model config
Debate rounds
Agent order
```

## Console

CheckpointAI 需要界面，但不是拖节点搭 workflow 的界面，而是审批台和实验复盘台。

V5.8-V5.15 已落地 Web Console：

```
V5.8: FastAPI console contract
V5.9: React P0 console
V5.10: serve / demo seed / E2E verification
V5.11-V5.15: Reports / Shadows / Safety hardening / Real data drill

已覆盖：
- Dashboard
- Approval Inbox / Detail
- Run History / Trigger / Detail
- Reports / Shadows
- Backup 管理
- Scenario scope 查看
- Adapter capability 查看

继续保持边界：
- 不做 Workflow Builder
- 不做 prompt 直接编辑器
- 不做 policy 规则编辑器
- 不做数据删除入口
```

```
Approval Inbox:
- prompt patch
- 策略进入模拟盘/实盘
- 工具策略变更
- 风控阈值变化
- 自媒体发布计划

Experiment Dashboard:
- 实验假设
- baseline
- 结果
- 有没有变好
- 失败原因

Run Viewer:
- 输入/输出
- agent trace
- 工具调用
- 成本/耗时/错误
- 最终指标

Version / Parameter Panel:
- prompt 版本
- 策略参数
- 工具配置
- 风控阈值
- 模型配置
```

Console 的目标不是让用户配置一切，而是让用户只处理需要判断力的事情。

---

## 当前进度

V1 已完成；V2.1-V2.11 已完成；V3.1-V3.4 已完成；V4.1-V4.5 已完成；V5.1-V5.15 已完成；V6.1-V6.4 已完成（低风险自治控制层：queue、audit-only process、operator feedback loop）。

| 版本 | 模块 | 文件 |
|---|---|---|
| V1.1 | Experiment Ledger | `checkpoint_ai/experiment/ledger.py` |
| V1.2 | Feedback Collector | `checkpoint_ai/experiment/feedback.py` |
| V1.3 | DataQualityGate | `checkpoint_ai/experiment/data_quality.py` |
| V1.4 | Baseline Compare | `checkpoint_ai/experiment/baseline.py` |
| V1.5 | RiskScore | `checkpoint_ai/experiment/risk_score.py` |
| V1.6 | LoopEngine | `checkpoint_ai/experiment/loop_engine.py` |
| V2.1 | Scenario + Adapter + Logs | `checkpoint_ai/scenario/`, `checkpoint_ai/adapter/`, `checkpoint_ai/logs/` |
| V2.2 | PromptVersionStore + PromptProposal | `checkpoint_ai/prompt/` |
| V2.3 | ScenarioPolicy | `checkpoint_ai/policy/` |
| V2.4 | ShadowRunner | `checkpoint_ai/shadow/` |
| V2.5 | AgentLoopEngine | `checkpoint_ai/loop/` |
| V2.6 | CLI + Report | `checkpoint_ai/v2_cli.py`, `checkpoint_ai/reporting.py` |
| V2.7 | First Demo Adapter | `checkpoint_ai/adapter/opc_agent_adapter.py` |
| V2.8 | V2 Stable | `tests/test_v28_v2_stable.py` |
| V2.9 | Quant Demo Data Run | `checkpoint_ai/adapter/quant_research_adapter.py` |
| V2.10 | Pre-V3 Data Contract Hardening | `checkpoint_ai/metrics/`, `checkpoint_ai/prompt/`, `checkpoint_ai/shadow/` |
| V2.11 | System Boundary Hardening | `docs/SYSTEM_BOUNDARIES.md`, `checkpoint_ai/control/`, `checkpoint_ai/policy/` |
| V3.1 | Evidence Evaluation | `checkpoint_ai/evaluation/evidence.py` |
| V3.2 | Scenario MetricSchema | `checkpoint_ai/metrics/store.py` |
| V3.3 | Version Recommender | `checkpoint_ai/recommendation/` |
| V3.4 | Bayesian Optimization Spike | `checkpoint_ai/optimization/` |
| V4.1 | Scenario Isolation Hardening | `checkpoint_ai/isolation/` |
| V4.2 | AdapterRegistry Hardening | `checkpoint_ai/adapter/capabilities.py` |
| V4.3 | Adapter Compatibility Contract | `checkpoint_ai/adapter/compatibility.py`, `docs/adapter_checklist.md` |
| V4.4 | Cross-Scenario Insight Preview | `checkpoint_ai/insights/` |
| V4.5 | V4 Stable | `tests/test_v45_v4_stable.py` |
| V4.6 | Systemic Hardening | `tests/test_v46_systemic_hardening.py` |
| V5.1 | Console Read Model | `checkpoint_ai/console/` |
| V5.2 | Approval Inbox | `checkpoint_ai/console/approval.py` |
| V5.3 | Run & Experiment Dashboard | `checkpoint_ai/console/dashboard.py` |
| V5.4 | Cost & Resource Control | `checkpoint_ai/console/cost.py` |
| V5.5 | Notification Routing | `checkpoint_ai/console/notification_routing.py` |
| V5.6 | Backup / Restore | `checkpoint_ai/console/backup.py` |
| V5.7 | V5 Stable | `tests/test_v52_v57_control_console.py` |
| V5.8 | Web Console API Contract | `checkpoint_ai/api.py`, `tests/test_v58_web_api.py` |
| V5.9 | React Control Console | `web/src/` |
| V5.10 | Console Tooling / Web Verification | `checkpoint_ai/demo.py`, `web/tests/e2e/` |
| V5.11 | Console API Hardening | `checkpoint_ai/api.py`, `tests/test_v511_v515_console_hardening.py` |
| V5.12 | Reports / Shadow Evidence Views | `web/src/features/reports/`, `web/src/features/shadows/` |
| V5.13 | Real Data Drill | `docs/V5_REAL_DATA_DRILL.md`, `docs/V5_REAL_DATA_DRILL_REPORT.md` |
| V5.14 | Operational Safety Hardening | `checkpoint_ai/console/backup.py`, `checkpoint_ai/api.py` |
| V5.15 | V5 Stable Acceptance | `docs/V5_STABLE_ACCEPTANCE.md` |
| V6.1 | Systemic Autonomy Safety Hardening | `checkpoint_ai/autonomy/`, `checkpoint_ai/events/` |
| V6.2 | Auto Action Queue Backend | `checkpoint_ai/autonomy/queue.py` |
| V6.3 | Autonomy Queue API + Web Console | `checkpoint_ai/api.py`, `web/src/features/autonomy/` |
| V6.4 | Operator Feedback Loop + V6 Stable | `checkpoint_ai/autonomy/`, `docs/V6_STABLE_ACCEPTANCE.md` |

历史调整：V1.7 Bandit 和 V1.8 Bayesian Optimization 移到 V3，因为它们需要真实 runs、多个 prompt 版本和足够观测。

---

## 路线

| 阶段 | 定位 | 通过标准 |
|---|---|---|
| V1 | Kernel 基础 | 已完成 |
| V2 | 安全优化闭环 | 能安全观察、提案、shadow、对比、回滚 |
| V3 | 证据驱动推荐 | 有 30+ 真实 runs 后，能基于证据推荐 |
| V4 | 隔离与可插拔验证 | 多场景/多 adapter 不污染，可降级 |
| V5 | 运营控制台 | 你能长期看懂、审批、报告、控成本 |
| V6 | 低风险自治 | 只自动处理已验证、可回滚、低风险动作 |

| 切换 | 条件 |
|---|---|
| V2.1 -> V2.2 | V2.1 十条验收全部通过 |
| V2 -> V3 | V2.8 稳定 + V2.9 至少一个 demo/real business line 有 30+ runs + V2.10/V2.11 数据契约和系统边界硬化完成 |
| V3 -> V4 | V3.5 稳定 + 出现第二个 business line 或 adapter 需求 |
| V4 -> V5 | V4.5 稳定 + 能回答"系统有没有变好" |
| V5 -> V6 | V5.15 稳定 + 真实数据演练通过 + 连续多次低风险 proposal 通过 shadow 且被人工批准 |

Post-V6 的 Team / Marketplace / Enterprise 不进入当前主线。

---

## V2 主线

| 版本 | 内容 | 重点 |
|---|---|---|
| V2.1 | Scenario + Adapter + Logs | 契约跑通 |
| V2.2 | PromptVersionStore + PromptProposal | 手动提案，不做 AI 自动生成 |
| V2.3 | Policy | BLOCKED 不跑 shadow，AUTO/APPROVAL 必须 shadow |
| V2.4 | ShadowRunner | shadow 不影响线上 |
| V2.5 | AgentLoopEngine | 已实现：单次事件闭环，不做永续黑箱 |
| V2.6 | CLI + Report | 已实现：能查清楚发生了什么 |
| V2.7 | First Demo Adapter | 已实现：用第一个真实 demo 贯穿验证 V2 闭环 |
| V2.8 | V2 Stable | 已实现：端到端验收 |
| V2.9 | Quant Demo Data Run | Pre-V3：用可重复量化场景积累真实可比较数据 |
| V2.10 | Data Contract Hardening | Pre-V3：修正 proposal、metric、comparison、run provenance 契约 |
| V2.11 | System Boundary Hardening | Pre-V3：澄清 control/policy、businessline/scenario、旧文档残留 |

V2.9 不是 V3，也不是 TradingAgents 正式适配。它只做一件事：用固定规则策略、固定合成数据和客观回测指标，验证 V2 的 experiment/log/proposal/policy/shadow/report 能否产出 V3 所需的数据。

```
V2.9 验收：
1. QuantResearchDemoAdapter 输出客观 metrics
2. metrics 至少包含 total_return / max_drawdown / sharpe / win_rate / trade_count / excess_return
3. CLI 和 report 能看到量化 demo 运行结果
4. V2 loop 能在量化 scenario 上跑 proposal -> policy -> shadow -> compare
5. 不做 Bandit、BO、自动生成 prompt、完整 TradingAgents 接入
```

V2.10 来自 V2.9 的 30 次数据运行暴露的问题。它不是新功能版本，而是进入 V3 前的数据契约修复。

```
V2.10 验收：
1. Proposal 不再只等于 PromptProposal；策略参数变化可以用通用 Proposal 表达
2. MetricSchema 定义 metric direction / category / weight / threshold
3. comparison 能区分 business metrics / system metrics / data quality metrics
4. max_drawdown lower-is-better，sharpe higher-is-better，不能再做裸 diff 判断
5. latency_ms / sample_count 不进入 business comparison
6. run_kind 标注 synthetic / historical / paper / live
7. provenance 记录 data_source / generated_by / seed / sample_count
8. policy 能根据 proposal type / magnitude / run_kind 做 AUTO / APPROVAL / BLOCKED
```

V2.11 来自 Pre-V3 系统扫描暴露的问题。它不是新闭环功能，而是防止旧模块边界混乱影响 V3。

```
V2.11 验收：
1. control/ 是 runtime action policy，policy/ 是 scenario proposal policy，二者边界明确
2. CheckpointAI facade 暴露 scenario_policy，不再只露旧 control policy
3. Scenario 可关联 business_line_id，但 Scenario 是 V2+ 优化域
4. 删除 V0 prompt 文档残留，避免规划混乱
5. 旧 V0.4 policy 测试改名为 runtime policy 测试
```

V2.7 不是 V2.8 前才开始做的最后一件事。它是贯穿 V2 的真实验证对象：V2.1 先用 DummyAdapter 跑通契约，后续每个 V2 模块都要逐步拿 First Demo Adapter 验证。

```
V2.1 验收：
1. 能创建 scenario
2. 能注册 dummy adapter
3. 能通过 scenario 运行 dummy adapter
4. dummy adapter 输出 answer + metrics
5. RawLog 保存完整输入输出
6. SummaryLog 保存 metrics + value_summary
7. 能按 scenario_id 查询日志
8. adapter 失败时有 failed summary
9. scenario 不存在时报明确错误
10. 系统能回答：这次运行的价值是什么
```

```
V2.2 Prompt 约束：
1. PromptProposal 以 patch 为主，不以整篇新 prompt 为主
2. PromptVersionStore 必须保存完整快照，确保可回滚
3. Prompt 按 slot 管理：role / goal / constraints / output_format / style / examples / tools_policy
4. 单次 proposal 默认只能改一个 slot
5. 小改 = patch；大改 = refactor proposal；重写只能作为 refactor proposal
6. refactor proposal 必须 shadow + baseline compare + human approval
7. prompt complexity_score 超阈值后，禁止继续 add，只允许 remove / replace / compress
8. 每 10 次 patch 或长度增长超过 30%，触发一次整理建议
```

```
V2.7 约束：
当前临时 demo: /Users/lemonsea/Desktop/mas/opc_agent
说明: opc_agent 只是当前临时实现，可删除、可重建；不要为它深度定制
接入方式: subprocess/API
禁止: 直接 import demo 的 Python 包结构
目的: 验证 adapter contract，而不是为 demo 深度定制
```

---

## V3-V6 边界

| 阶段 | 做什么 | 不做什么 |
|---|---|---|
| V3 | Evidence-Based Recommendation：MetricSchema、Evaluation、推荐 prompt 版本、可选 BO | 不从小样本假装学习 |
| V4 | Scenario isolation + AdapterRegistry + compatibility checklist | 不为了外部框架做深度 fork |
| V5 | Control panel、Approval inbox、Report、Notification、Cost/resource control、Backup/restore | 不做复杂企业平台 |
| V6 | Safe auto-execution、self-healing、experiment scheduling、policy preference suggestions | 不完全无人值守，不自动上线高风险策略 |

---

## V5 主线

V5 的核心不是先做网页，而是先做“人每天能看的控制台语义”。UI 只能读取 read model，不能直接拼各个 store。

V5 前置隐患修复：

```
1. report latest 不能隐式跨 scenario
2. archived scenario 不能启动新 run
3. prompt proposal 和 generic proposal 必须能进入统一 pending view
4. console read model 默认 scope-aware，跨场景必须显式 reason
```

V5 顺序：

| 版本 | 内容 | 重点 |
|---|---|---|
| V5.1 | Console Read Model | 已实现：统一 scenario/run/pending snapshot |
| V5.2 | Approval Inbox | 已实现：聚合 prompt / strategy / recommendation / parameter 待审批项 |
| V5.3 | Run & Experiment Dashboard | 已实现：回答为什么跑、发生什么、有没有变好 |
| V5.4 | Cost & Resource Control | 已实现：成本事件持久化、日度 summary |
| V5.5 | Notification Routing | 已实现：只推送需要人判断的审批/告警/报告 |
| V5.6 | Backup / Restore | 已实现：SQLite 可恢复备份，restore 前 safety backup |
| V5.7 | V5 Stable | 已实现：snapshot + inbox + cost + backup 串联 |
| V5.8 | Web Console Usability Hardening | 已实现：token 校验、scenario 切换、patch 视图、restore 确认 |
| V5.9 | Web API and Control Console | 已实现：FastAPI API、React Console |
| V5.10 | Console Tooling and Web Verification | 已实现：serve/demo seed、E2E、首屏验证 |
| V5.11-V5.15 | Console API Hardening + Real Data Drill | 已实现：Reports、Shadows、Approval 加强、Backup 加强、真实数据演练 |

---

## V5 最终版定义

V5 最终版 = 人类控制台生产可用。

不是自动执行，不是新算法，不是 TradingAgents 深接入。

V5 只解决一个问题：你打开控制台，能清楚看到系统在干什么、哪里要你判断、为什么要判断、判断后能安全记录和回滚。

---

## V5.8-V5.15 详细内容

### V5.8: Web Console API Contract

目标：让控制台有稳定、受 Bearer Token 保护的后端契约。

已实现：
- Dashboard snapshot API
- Approval list/detail/approve/reject API
- Run list/detail/trigger API
- Backup list/create/restore API
- Scenario list/show/archive API
- Adapter capability API
- Health API
- API auth 从 `CHECKPOINTAI_API_TOKENS` / `CHECKPOINTAI_API_TOKEN` 读取

### V5.9: Web API and Control Console

目标：FastAPI 后端 + React 前端控制台基础框架。

已实现：
- FastAPI console API endpoints
- React + Vite + shadcn/ui 控制台
- Dashboard / Approval Inbox / Run History / Backup

### V5.10: Console Tooling and Web Verification

目标：工具链 + 验证。

已实现：
- checkpointai api serve
- checkpointai demo seed-console
- npm run e2e (Playwright 首屏验证)

### V5.11-V5.12: Reports + Evidence Views + Shadows

目标：让控制台能完整回答"为什么运行、发生了什么、有没有变好"。

已实现：
- GET /api/version
- GET /api/auth/check
- GET /api/reports/latest
- GET /api/reports/runs/{id}
- GET /api/reports/proposals/{id}
- GET /api/reports/recommendations/{id}
- GET /api/shadows
- GET /api/shadows/{id}
- POST /api/shadows
- Web Reports 页面
- Shadow Result 页面
- Approval Detail before/after patch 视图
- Run Trigger 根据 adapter task types 选择任务

### V5.13: Real Data Drill

目标：用真实数据验证控制台不是摆设。

已实现：
- demo seed-console
- quant demo 30 runs
- synthetic proposal/shadow/recommendation flow
- 生成 `docs/V5_REAL_DATA_DRILL_REPORT.md`

验收：至少 30 条 run 数据进入控制台。

### V5.14: Operational Safety Hardening

目标：把人为误操作风险降下来。

已实现：
- approve/reject 必须写 comment
- 已处理 approval 不允许重复处理
- restore 前自动创建 pre-restore backup
- 危险操作二次确认
- Backup restore 必须输入 `RESTORE`

仍需 V6 前观察：
- 错误响应还没有完全统一成一个 envelope
- Approval comment 目前用于操作要求，尚未沉淀成完整 audit comment log

### V5.15: V5 Stable

目标：V5 完整验收，不做新功能。

已实现：
- 全量测试：unittest / ruff / mypy / npm lint / npm build / E2E
- 文档：Web Console 使用手册、本地启动手册、V5 验收报告

验收：可以只靠 Web Console 完成一次完整操作，不需要打开 DB 或读 CLI 输出。

---

## V5 完成后才能进 V6 的条件

必须满足：
- Web Console 能稳定显示真实 run/proposal/report
- Approval Inbox 能真正辅助判断
- Backup/restore 可靠
- 所有危险操作有 audit trail
- E2E 覆盖核心链路
- 真实数据演练后没有结构性缺口
- 能在 UI 上看懂系统为什么建议改

---

## V5 不做什么

- 自动执行低风险 proposal
- 自动调度实验
- 自动改 prompt
- TradingAgents 正式接入
- Workflow Builder
- Prompt 编辑器
- Policy 编辑器
- 多用户权限系统
- 复杂图表大屏

这些属于 V6 或之后。

---

## V5 后风险审查

完整风险审查见 `docs/V5_RISK_REVIEW.md`。

结论：
- 可以进入 V6 规划。
- 不能直接进入自动执行。
- V6 第一优先级必须是 `DecisionLog`、统一错误契约、checkpoint 协议和 action log。

---

## V6 主线

完整 V6 规划见 `docs/V6_PLAN.md`；风险收口见 `docs/V6_RISK_REVIEW.md`；验收清单见 `docs/V6_STABLE_ACCEPTANCE.md`。

V6 的核心是“低风险自治”，不是“AI 自己决定一切”。

V6 只允许系统自动处理：已有 proposal、已通过 shadow/replay、证据足够、风险低、可回滚、有 checkpoint、有完整 action log 的动作。

V6 不允许系统自动处理：高风险策略上线、大幅 prompt 重写、生产发布、实盘交易、跨场景迁移、删除历史数据。

V6 当前实现保持 `audit_only` process drill：控制台可处理队列并写审计记录，但不会真实修改 prompt、策略或部署。

---

## V5 历史验收补充

```
1. ConsoleReadModel 能生成 scope-aware snapshot
2. snapshot 包含 scenario count、active/archive、recent runs、failed runs、pending approvals
3. CLI 能输出 console snapshot
4. 默认不隐式跨 scenario
5. 跨 scenario 必须传 allow_cross_scenario + reason
```

V5.15 后进入 V6 的准备状态：

```
已经具备：
- 统一 ApprovalInbox，可让 V6 自动执行前先判断是否需要人工
- CostEventStore，可让 V6 根据持久成本状态做预算约束
- ConsoleDashboard，可让 V6 每次自动动作后生成可解释报告
- BackupManager，可让 V6 自动动作前创建恢复点
- NotificationRouter，可让 V6 只推送需要人处理的事件

仍然不做：
- 高风险自动上线
- 自动跨场景迁移
- 自动修改 TradingAgents/CrewAI
- 多用户企业权限
```

---

## V4 主线

V4 的核心是“隔离与可插拔能力验证”，不是接入更多外部框架。

Hermes 讨论结论：

```
1. Scenario 有 archive，不做物理 delete；delete 留在 BusinessLine 层面
2. Cross-scenario insight 的 tags 人工填为主，自动推断为辅
3. Adapter compatibility report 同时写文档和 SQLite
4. Adapter capabilities 在 V4.2 强制结构化，废弃 dict 兼容
5. TradingAgents/CrewAI spike 放在 V4.5 之后
```

V4 顺序：

| 版本 | 内容 | 状态 |
|---|---|---|
| V4.1 | Scenario Isolation Hardening | 已实现：ScenarioScope、archive、IsolationAuditor |
| V4.2 | AdapterRegistry Hardening | 已实现：结构化 capabilities、registry 查询、unsupported shadow 显式失败 |
| V4.3 | Adapter Compatibility Contract | 已实现：兼容性 evaluator、SQLite report store、adapter checklist 文档 |
| V4.4 | Cross-Scenario Insight Preview | 已实现：preview-only insight，真实 evidence 不足时拒绝 |
| V4.5 | V4 Stable | 已实现：多 scenario、多 adapter、隔离、兼容性、insight 端到端测试 |

V4 约束：

```
1. 不正式适配 TradingAgents/CrewAI
2. 不自动跨场景迁移 prompt、参数、策略、policy
3. 不允许 hidden global query；跨场景必须显式
4. Adapter 不支持的能力必须明确降级
5. Synthetic evidence 只能验证链路，不能支撑 cross-scenario insight
```

---

## V3 主线

V3 的核心不是“开始强化学习”，而是先建立证据判断层：系统必须能判断一次 comparison 是否足够支持推荐。

```
V3.1 Evidence Evaluation：
输入：ComparisonResult
输出：improved / worse / inconclusive
同时输出：confidence、reason、guardrail_violations、recommended_action
```

V3.1 规则：

```
1. synthetic run 即使指标变好，也只能是 inconclusive
2. guardrail violation 直接 worse / reject
3. sample_count 不足则 inconclusive
4. objective_score 负向则 worse / reject
5. 只有 historical / paper / live 且样本足够、置信度足够，才允许 improved
```

这保证系统不会把“能跑通的 demo 数据”误读成“策略真的变好”。

V3 顺序：

| 版本 | 内容 | 前提 |
|---|---|---|
| V3.1 | Evidence Evaluation | 已实现：能判断 improved / worse / inconclusive |
| V3.2 | Scenario MetricSchema 持久化和评估报告增强 | 已实现：scenario 有独立 metric schema，报告显示 evidence |
| V3.3 | Prompt/Strategy Version Recommender | 已实现：只在已有 shadow evidence 里做推荐，不生成 proposal |
| V3.4 | Bayesian Optimization Spike | 已实现：只建议连续参数候选值，不自动执行 |
| V3.5 | V3 Stable | 推荐只基于可解释证据，不从 synthetic 小样本假装学习 |

V3.3 约束：

```
1. Recommendation 是可审计对象，不是执行动作
2. 只推荐已有 proposal/shadow result，不生成新 prompt
3. synthetic run 必须 insufficient_evidence
4. guardrail violation 必须 reject
5. human accept/reject 只改变 recommendation status，不自动改线上配置
```

V3.4 约束：

```
1. Bayesian Optimization 只是 spike，不是生产级优化器
2. 只处理一维连续参数，输入必须显式给 observations
3. 输出 ParameterSuggestion，不执行、不部署、不改 proposal
4. 样本不足时只做 midpoint exploration
5. suggestion accept/reject 只改变状态，不触发线上变更
```

---

## 技术原则

```
1. 所有优化必须可回溯
2. 所有自动化必须先 shadow
3. 低质量数据不能用于判断
4. 跨场景只迁移经验，不迁移参数
5. 先规则，再算法
6. 每个阶段必须有价值验收
```

---

## 能力边界

```
一定要做到：
- 记录、评估、对比、回滚
- 改了以后知道有没有变好
- 少犯重复错误

大概率能做到：
- 基于证据给建议
- 哪个 prompt 更稳
- 哪些实验没必要重复

谨慎对待：
- 自动发现机会、自动提出高质量改法、持续变聪明
- 数据量小、指标不稳定、内容质量主观

不应该做：
- 追求"AI 自动强化学习、越跑越聪明"
- 承诺"80% 自动优化"
- 假装从少量数据中学到规律
```

---

## 真正目标

```
不要问：能不能做成自动进化系统？
要问：能不能让我每次改 Agent / 工作流都知道有没有变好？
如果这个成立，CheckpointAI 就有根了。
```

---

## 核心创新

**CheckpointAI 的创新是架构上的，不是某个 Agent 实现里的。**

```
Agent 实现 = 会做某件事
CheckpointAI 架构 = 让"会做某件事的 Agent"持续变好
```

比喻：
```
Agent = 员工
Business Team Runtime = 办公室/工作流，最终以代码系统为主
CheckpointAI = 绩效复盘 + 实验管理 + 改进制度 + 审批台
```

Agent 只需要暴露可调参数：prompt slots、model config、tools config、strategy parameters
CheckpointAI 负责：观察结果、发现问题、提出 patch、跑 shadow、比较 baseline、记录版本

```
1. Experiment Ledger
   每次 Agent 改动都不是随便改，而是有假设、baseline、结果、结论

2. Prompt Patch，而不是 Prompt 重写
   不让 prompt 越改越乱，不允许大改失控

3. Shadow + Baseline Compare
   新版本先和旧版本对比，不直接上线

4. Evidence Gate
   数据不够时，系统只能观察，不能假装学习

5. Scenario Optimization
   不同业务线用不同指标优化：量化看收益/回撤/稳定性，自媒体看播放/互动/关注

创新点不在代码复杂度，而在工作流纪律

如果你把 CheckpointAI 又做成 Workflow Builder，那就没创新了
如果它专注做"Agent 有没有变好"的判断层，它就有价值
```
