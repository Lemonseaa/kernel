# V5 Risk Review

## Conclusion

V5 可以作为控制台阶段收口。V6 第一批 P0 风险已经完成基础代码修复：审计、错误契约、checkpoint/action log、eligibility gate 已落地。仍不能直接进入无人值守，后续只能按 V6 queue 和反馈闭环继续推进。

## P0 Risks

这些风险会阻止 V6 自动执行能力上线。

| 风险 | 当前状态 | 代码位置 |
|---|---|---|
| Decision audit 不完整 | 已修复：approve/reject、restore failure/success、shadow failure 写入 decision log | `loop_harness/decision/`, `loop_harness/api.py` |
| API error shape 不统一 | 已修复：FastAPI HTTPException 统一返回 `{code, message, details}`，Web UI 读取 envelope message | `loop_harness/api.py`, `web/src/api/client.ts` |
| 自动动作没有 checkpoint 协议 | 已修复基础协议：autonomy action 必须带 checkpoint_id | `loop_harness/autonomy/` |
| 自动动作没有 action ledger | 已修复：新增 `AutonomyActionStore`，支持状态和 rollback 记录 | `loop_harness/autonomy/store.py` |
| low-risk 定义不够硬 | 已修复：新增 `AutoExecutionEligibility`，拒绝 synthetic、guardrail violation、missing checkpoint 等 | `loop_harness/autonomy/eligibility.py` |

## P1 Risks

这些风险不阻止 V6，但会影响运营体验。

| 风险 | 当前状态 | 处理方式 |
|---|---|---|
| Report 主要是文本 | 可读，但趋势和对比不够直观 | V6 后半段做轻量趋势图 |
| Shadow 需要手填 proposal_id | 可用，但不够顺手 | V6.4 从 Approval Detail 触发 shadow |
| Metric schema 还没有 UI | 后端和 CLI 已有 | V6 暂不开放 UI 编辑，避免配错指标 |
| E2E 覆盖偏浅 | 首屏/nav 可验证，核心 API 有 unittest，前端已统一展示 API error message | 后续增加更多 API mock E2E |

## V6 不应该解决

- 多用户企业权限
- TradingAgents/CrewAI 深度适配
- Workflow Builder
- 自动生成大段 prompt
- 自动实盘交易或自动发布

这些会把 V6 拖成企业平台或黑箱自治，偏离 LoopHarness 的主线。

## Go / No-Go

可以进入 V6 规划：

- V5 控制台已经能处理 approval、runs、reports、shadows、backup。
- 30 次 quant demo drill 已生成报告。
- P0 风险已有基础修复，后续可以进入 queue 和 feedback loop。

仍不能进入无人值守：

- 还没有 Auto Action Queue processor
- 还没有 Web Console action queue view
- 还没有 Operator Feedback Loop
- 还没有真实 historical 数据的低风险自动动作演练
