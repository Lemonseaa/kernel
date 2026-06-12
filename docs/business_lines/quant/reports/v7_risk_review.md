# V7 Risk Review

## Reviewed Risks

### 1. Agent自由决策越权

Mitigation: V7 only produces candidates, shadow jobs, validation summaries, and approval-ready evidence. `LearningLoopService` returns `applied_count=0`.

### 2. Prompt越改越长

Mitigation: V7 proposer output is patch-first. Full rewrite is not part of the normal proposer path.

### 3. Hermes草稿污染正式偏好

Mitigation: `UserProfileStore` separates `USER_PROFILE.md` from `SUGGESTED_PROFILE_NOTES.md`. `AgentRuntimeContextBuilder` exposes formal profile separately and does not merge Hermes notes into formal constraints.

### 4. 多业务线或多场景污染

Mitigation: V7 blackboard objects require `business_line_id` and `scenario_id`. Stores query by scope and tests assert wrong-scenario reads return empty.

### 5. Shadow结果误当真实部署

Mitigation: `ShadowReplayScheduler` creates `apply_requested=False` jobs only. Validator recommendations are advisory.

### 6. 配置版本不可回滚

Mitigation: `ConfigVersionService` supports lock, branch, active branch switching, and rollback to locked versions.

### 7. 重复提案互相冲突

Mitigation: `ConflictDetector` keeps one proposal per target per tick.

## Residual Risks

- V7 drill uses deterministic historical-like data, not live production data.
- Safety rules are intentionally conservative and simple; V8 can add richer historical success-rate scoring.
- UI integration for V7 objects should be added after the backend contract stabilizes further.
