# V6 Risk Review

## Conclusion

V6 可以收口为“低风险自治控制层”，但不能描述为无人值守自动执行系统。

当前实现允许：

- 记录满足条件的 autonomy action
- 持久化暂停/恢复队列
- 在控制台查看 action、checkpoint、reason、status、result
- 通过 audit-only process drill 验证队列和审计链路
- 从 operator approve/reject 历史生成 policy proposal

当前实现不允许：

- 自动修改真实 prompt
- 自动切换真实策略
- 自动发内容
- 自动实盘交易
- 自动放宽 policy
- 自动跨场景迁移经验

## Risk Sweep

| Risk | Status | Handling |
|---|---|---|
| Queue pause state only in memory | Fixed | `AutonomyQueueStateStore` persists pause/resume in SQLite |
| API process endpoint might apply live changes accidentally | Controlled | Handler is audit-only and returns `applied=false` |
| Queue process by id could process oldest item instead | Fixed | `AutoActionQueue.process(action_id, handler)` processes the selected item |
| Feedback loop might self-relax policy | Controlled | `OperatorFeedbackAnalyzer` only creates `policy_proposal` for Approval Inbox |
| Synthetic evidence could trigger autonomy | Guarded | `AutoExecutionEligibility` rejects synthetic evidence |
| Missing checkpoint could trigger autonomy | Guarded | action log requires `checkpoint_id`; eligibility rejects missing checkpoint |
| Web Console could hide failures | Controlled | API errors use `{code,message,details}` and UI displays envelope message |
| Backup restore could erase decision history | Controlled | restore path preserves prior decision records for the restore source |

## Residual Risks

| Residual Risk | Why It Remains | Next Step |
|---|---|---|
| No real safe-apply implementation | V6 intentionally avoids live mutation | V7 can add adapter-specific safe apply after real business adapter hardening |
| Rollback processor is not wired to real adapters | No live apply exists yet | Implement together with real safe apply, not before |
| Policy proposal thresholds are simple | Data volume is still small | Tune after repeated real operator decisions |
| Web UI is control-first, not analytics-rich | V6 prioritizes safety and visibility | Add trend charts only after real data volume grows |

## Production Boundary

V6 is suitable for local/operator-supervised drills and control-plane validation.

V6 is not suitable for:

- real capital deployment
- production content publishing
- unattended policy evolution
- deleting or rewriting historical records

Any future live execution must pass three gates:

1. adapter declares `safe_apply` support
2. action has checkpoint and rollback path
3. operator explicitly approves the first live runs for that scenario
