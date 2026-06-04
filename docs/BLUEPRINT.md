# CheckpointAI Blueprint

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

V1 已完成；V2.1、V2.2、V2.3、V2.4、V2.5、V2.6、V2.7 已实现；当前准备进入 V2.8。

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
| V2 -> V3 | V2.8 稳定 + 至少一个 demo/real business line 有 30+ 真实 runs |
| V3 -> V4 | V3.5 稳定 + 出现第二个 business line 或 adapter 需求 |
| V4 -> V5 | V4.5 稳定 + 能回答"系统有没有变好" |
| V5 -> V6 | V5.8 稳定 + 连续多次低风险 proposal 通过 shadow 且被人工批准 |

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
| V2.8 | V2 Stable | 端到端验收 |

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
