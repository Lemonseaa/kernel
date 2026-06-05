# V6 Plan

## Positioning

V6 = low-risk autonomy.

不是让 CheckpointAI 自己决定一切，而是让它自动处理满足严格条件、已经验证、可回滚的低风险动作。

## V6 Allowed Actions

系统只允许自动处理：

- 已存在的 proposal 或 accepted recommendation
- 已通过 shadow / replay
- 有足够非 synthetic evidence
- 无 guardrail violation
- 风险低
- 可回滚
- 已创建 checkpoint
- 有完整 action log

系统不允许自动处理：

- 高风险策略上线
- 大幅 prompt 重写
- 生产发布
- 实盘交易
- 跨场景迁移
- 删除历史数据

## Version Breakdown

### V6.1: Decision Log + API Error Envelope

目标：所有人类决策、系统拒绝、API 错误都可查询、可展示。

状态：已完成基础实现；Web UI 已接入统一错误 message 展示。

必须实现：

- `DecisionLog`
- `ApiError` response model
- approve/reject/comment 写入 decision log
- blocked policy / failed shadow / failed restore 写入 decision 或 error record
- Web UI 统一错误展示

验收：

- Approval comment 可查询
- API 错误统一返回 `{code, message, details}`
- 前端不再只显示 axios 原始错误

### V6.2: Auto-Action Checkpoint Protocol

目标：任何自动动作执行前必须有恢复点。

状态：已完成基础 action log 和 checkpoint_id 强制要求；真实 queue 执行和 rollback processor 仍在 V6.4。

必须实现：

- auto action 前创建 checkpoint / backup
- action record 关联 checkpoint id
- action failed 时支持 rollback
- action report 回答：为什么自动执行、恢复点在哪、结果如何

验收：

- 没有 checkpoint 的 auto action 被拒绝
- 自动动作失败后能回滚
- Web Console 能看到 checkpoint id

### V6.3: AutoExecutionEligibility

目标：把“低风险可自动执行”的条件硬编码成可测试规则。

状态：已完成基础规则 gate。

规则：

- proposal status 必须是 approved，或 recommendation status 必须 accepted
- shadow passed
- run_kind 至少 historical；synthetic 永远不能 auto-apply
- no guardrail violation
- risk score 低于阈值
- patch magnitude 小
- adapter capability 支持 safe apply
- checkpoint 已创建

验收：

- synthetic evidence 不触发 auto-apply
- guardrail violation 不触发 auto-apply
- missing checkpoint 不触发 auto-apply
- 满足所有条件的 low-risk patch 进入 auto action queue

### V6.4: Auto Action Queue

目标：低风险动作可排队执行，并且每一步可暂停、可审计、可撤销。

必须实现：

- queue item model
- queue store
- queue processor
- pause/resume
- Web Console queue view

状态：

- pending
- running
- succeeded
- failed
- rolled_back

验收：

- queue item 有 scenario_id / proposal_id / action_type / checkpoint_id / reason
- queue 执行结果进入 action log
- Web Console 能看到队列和结果

### V6.5: Operator Feedback Loop

目标：从人类审批历史里学习偏好，但只生成 policy suggestion，不自动改 policy。

必须实现：

- 统计同类 proposal 的 approve/reject 分布
- 生成 policy suggestion report
- policy suggestion 进入 Approval Inbox
- 人类批准后才允许改 policy

验收：

- 系统能解释“为什么建议放宽/收紧”
- policy suggestion 不会自动应用

### V6.6: V6 Stable

目标：低风险自治可用，但人类仍然掌握上线和高风险决策。

验收：

- 连续 20 次 synthetic/historical 混合测试中，synthetic 不触发 auto-apply
- 至少 5 次 historical low-risk auto action 成功执行并有 checkpoint
- 任一失败 action 可回滚
- Web Console 可查看 action log / decision log / checkpoint / report
- 全量 unittest / ruff / mypy / frontend lint/build/e2e 通过

## V6 Implementation Order

1. V6.1 DecisionLog 和 API 错误契约（基础完成）
2. V6.2 checkpoint 协议和 action log（基础完成）
3. V6.3 eligibility gate（基础完成）
4. V6.4 queue（下一步）
5. V6.5 feedback loop
6. V6.6 stable acceptance

## V6 Non-Goals

- 不自动实盘
- 不自动发内容
- 不做 TradingAgents 正式适配
- 不做 Workflow Builder
- 不做多用户企业权限
- 不做 prompt 全文重写器

## V7+ Direction

- V7: Real business adapter hardening，量化或内容二选一
- V8: TradingAgents spike / adapter feasibility
- V9: Prompt optimizer，只做 patch proposal
- V10: Production deployment guardrails
