# CheckpointAI Web UI Plan

## 核心原则

```
不要先做前端页面。先做 Web API + Console 数据契约。
如果直接写 React，会变成前端到处拼 store，后面一定返工。
```

---

## 原则

```
UI 只做控制台，不做工作流编辑器
所有危险操作必须二次确认
所有 approve/reject 必须能写 comment
所有列表默认按 scenario scope
跨 scenario 视图必须显式标记
前端不直接编辑 prompt，只展示 patch
前端不直接改 policy
前端不删除历史数据
```

---

## Phase 0: Web API Contract

先做后端 API，作为控制台专用接口。

### 当前实现状态

```
V5.8-V5.15 已实现：
- Bearer Token 保护的 console API
- Dashboard snapshot
- Approval list/detail/approve/reject
- Approval 动作强制 comment，已处理项不能重复处理
- Run list/detail/trigger
- Backup list/create/restore
- Restore 强制 `confirm=RESTORE`，恢复前创建 safety backup
- Scenario list/show/archive
- Adapter capability list
- Health endpoint
- Version/auth check endpoint
- Shadow list/detail/run API
- Reports latest/run/proposal/recommendation API
```

### API Endpoints

```
GET  /api/console/snapshot
GET  /api/approvals
GET  /api/approvals/{id}
POST /api/approvals/{id}/approve
POST /api/approvals/{id}/reject

GET  /api/runs
GET  /api/runs/{id}
POST /api/runs

GET  /api/shadows
GET  /api/shadows/{id}
POST /api/shadows

GET  /api/reports/latest
GET  /api/reports/runs/{id}
GET  /api/reports/proposals/{id}

GET  /api/backups
POST /api/backups
POST /api/backups/{id}/restore

GET  /api/scenarios
GET  /api/scenarios/{id}
POST /api/scenarios/{id}/archive

GET  /api/adapters
GET  /api/health
```

---

## Phase 1: P0 UI

做能每天用的控制台。

### 当前实现状态

```
V5.9 P0/P1基础已实现：
- Dashboard
- Approval Inbox
- Approval Detail + approve/reject/comment
- Run History
- Trigger Run
- Run Detail
- Backup 管理
- Scenario 只读列表 + scope选择 + archive
- Adapter capabilities 只读查看

V5.10 工具已补：
- `checkpointai api serve` 启动 FastAPI 控制台 API
- `checkpointai demo seed-console` 生成可操作的 demo scenario/run/proposal/backup
- `npm run lint` 检查 React/TypeScript 代码
- `npm run format:check` 检查前端格式
- `npm run e2e` 用 Playwright + 系统 Chrome 验证控制台首屏

V5.11-V5.15 已补：
- Reports 页面：latest/run/proposal 证据报告
- Shadows 页面：触发 shadow、查看 shadow history
- Approval Detail 展示 patch before/after
- Trigger Run 根据 adapter supported_task_types 选择任务
- Restore 需要输入 `RESTORE`

仍不做：
- Workflow Builder
- 代码编辑器
- prompt 直接编辑器
- policy 规则编辑器
- 历史数据删除
```

### Dashboard

```
顶部：系统健康、pending approvals、failed runs、今日成本
中部：scenario 状态表
下部：recent runs、latest recommendations、成本摘要

重点不是炫图，是"今天我该处理什么"
```

### Approval Inbox（第一核心页）

```
列表字段：
- type
- scenario
- title
- reason
- expected_metric
- risk/evidence
- age
- status

详情页必须展示：
- 改了什么
- 为什么改
- 期望改善什么指标
- shadow 对比
- evidence 是否足够
- approve / reject / comment
```

### Runs

```
- run history
- run detail
- 手动触发 run
- 显示 task/context/config

不要做成复杂 workflow builder
```

---

## Phase 2: P1 UI

### Shadow

```
- proposal 列表
- shadow result
- baseline vs candidate
- business metrics / system metrics 分开显示
```

### Reports

```
- run report
- proposal report
- recommendation report
- cost report

重点是可读文本 + 少量图表，不是 BI 大屏
```

### Backup

```
- backup list
- create backup
- restore 二次确认
- restore 前显示风险提示
```

---

## Phase 3: P2 UI

### Scenario 管理

```
- 创建 scenario
- 修改 name / description / metadata / tags
- archive
- 查看 scenario 下 runs / proposals / metrics
```

### Metric Schema

```
- 查看/编辑 metric
- direction / category / weight / threshold

这个要谨慎，因为配错会影响系统判断
```

### Adapter

```
- 查看 adapter capabilities
- 查看 compatibility report
- 不允许编辑 adapter 代码
```

---

## 技术栈

```
Backend: FastAPI
Frontend: React + Vite
UI: Tailwind + shadcn/ui
State: Zustand（UI状态，如当前scenario、筛选条件、侧边栏状态）
HTTP: TanStack Query（替代手写Zustand异步状态）
Charts: 先用轻量 SVG components，复杂后再引入 Recharts
Tables: TanStack Table
E2E: Playwright（优先使用本机 Chrome channel，避免强依赖浏览器下载）
```

## V7.9 新增重点

### 1. Workflow Map

目标：把外部工作流从黑盒变成可视化、可审计、可诊断的结构图。

页面/组件：

```
web/src/features/workflow-map/
├── WorkflowOverviewPage.tsx
├── RunTracePage.tsx
├── NodeDetailPanel.tsx
├── WorkflowDiffPage.tsx
└── TraceCoveragePanel.tsx

web/src/components/workflow/
├── WorkflowGraph.tsx
├── WorkflowNodeCard.tsx
├── WorkflowEdgeLayer.tsx
├── StageMap.tsx
└── OptimizationOverlay.tsx
```

后端 API：

```
GET /api/workflows
GET /api/workflows/{workflow_id}/manifest
GET /api/workflows/{workflow_id}/map
GET /api/workflows/{workflow_id}/coverage
GET /api/workflows/{workflow_id}/diff
GET /api/runs/{run_id}/workflow-trace
GET /api/workflow-nodes/{node_id}
```

硬规则：

```
1. Workflow Map 不是编辑器
2. 控制流和数据流必须区分
3. node 必须显示类型、状态、成本、耗时、风险、可优化项
4. 黑盒节点必须明显标注
5. 低 Trace Coverage 不能进入自动优化
```

### 2. Workflow Design Assistant

目标：用表格梳理 + 模式推荐 + 草图生成，帮助用户生成可被 CheckpointAI 管理的工作流草案。

页面/组件：

```
web/src/features/workflow-design/
├── IntentTablePage.tsx
├── MethodologyFormPage.tsx
├── StageMapDraftPage.tsx
├── PatternRecommendationPage.tsx
├── WorkflowDraftPage.tsx
└── ManifestPreviewPage.tsx
```

流程：

```
Intent Table
  -> Methodology Form
  -> Stage Map
  -> Pattern Recommendation
  -> Workflow Draft
  -> Manifest Preview
```

Pattern 不是全局选择，而是每个阶段的局部推荐。

支持混合：

```
Sequential / Parallel Exploration / Supervisor Dispatch / Critic-Refine
Voting / Debate / Tournament / Champion-Challenger / Human Gate
Data Quality Gate / Shadow Replay / Fallback / Budget Gate
Router / Conditional Branch / Ensemble / A/B Test / Simulation Loop
```

### 3. Methodology Profile

目标：让用户显式定义自己的审美、风险偏好、判断标准和行业方法论。

页面/组件：

```
web/src/features/methodology/
├── MethodologyProfileListPage.tsx
├── MethodologyProfileDetailPage.tsx
├── MethodologyProfileEditor.tsx
└── MethodologyAlignmentPanel.tsx
```

硬规则：

```
1. 人类确认后才成为正式 Methodology Profile
2. Hermes 只能生成建议草稿
3. Agent 不可自动修改
4. Proposal Detail 必须显示 Methodology Alignment
5. 违反方法论的 proposal 即使指标提升，也不能自动通过
```

### 4. Optimization Visualization

目标：每次修改后的效果必须用图表直观展示。

页面/组件：

```
web/src/features/visualizations/
├── ProposalImpactPage.tsx
├── ScenarioMetricTrendPage.tsx
├── VersionPerformancePage.tsx
└── ProposalQualityPage.tsx

web/src/components/charts/
├── MetricBarChart.tsx
├── MetricTrendChart.tsx
├── ImprovementDeltaChart.tsx
└── OutcomeDistributionChart.tsx
```

后端 API：

```
GET /api/visualizations/proposals/{proposal_id}/impact
GET /api/visualizations/scenarios/{scenario_id}/metrics
GET /api/visualizations/scenarios/{scenario_id}/proposal-quality
GET /api/visualizations/config-versions/performance
```

硬规则：

```
1. business metrics 和 system metrics 分开
2. 图表必须显示 run_kind
3. synthetic evidence 必须标 advisory
4. 颜色方向必须尊重 MetricSchema
```

### 5. LLM Provider Console

目标：从 env-only 配置升级为可视化模型厂商操作台。

页面/组件：

```
web/src/features/llm/
├── ProviderListPage.tsx
├── ProviderDetailPage.tsx
├── ModelListPage.tsx
├── RoleRoutingPage.tsx
└── ProviderHealthPage.tsx
```

后端 API：

```
GET /api/llm/providers
POST /api/llm/providers
PATCH /api/llm/providers/{provider_id}
POST /api/llm/providers/{provider_id}/test
GET /api/llm/models
POST /api/llm/models
PATCH /api/llm/models/{model_id}
GET /api/llm/routing
PATCH /api/llm/routing/{role}
GET /api/llm/health
GET /api/llm/costs
```

安全规则：

```
1. UI 不显示明文 API key
2. disabled provider 不能被 router 选择
3. 超预算 provider 不能进入自动探索
4. provider health 失败时必须降级或提示
```

## 本地启动

```
# 1. 准备 demo 数据
checkpointai --db .runtime/console_demo.db demo seed-console --backup-dir .runtime/backups

# 2. 启动 API
CHECKPOINTAI_API_TOKENS=dev-token checkpointai --db .runtime/console_demo.db api serve --host 127.0.0.1 --port 8000

# 3. 启动前端
cd web
npm install
npm run dev -- --host 127.0.0.1
```

前端需要 Bearer Token。本地开发可在输入框填 `dev-token`。生产环境必须使用更长的随机 token，并通过 `CHECKPOINTAI_API_TOKENS` 注入。

---

## 前端目录结构

```
web/
├── src/
│   ├── app/
│   ├── api/
│   ├── components/
│   ├── features/
│   │   ├── dashboard/
│   │   ├── approvals/
│   │   ├── runs/
│   │   ├── shadows/
│   │   ├── reports/
│   │   ├── backups/
│   │   ├── scenarios/
│   │   └── adapters/
│   ├── lib/
│   └── types/
```

---

## 优先级

```
P0（必须有）：
1. FastAPI console endpoints
2. Dashboard
3. Approval Inbox
4. Approval Detail
5. Run History
6. Trigger Run

P1（重要）：
7. Shadow Result
8. Reports
9. Backup
10. Workflow Map
11. Workflow Design Assistant
12. Methodology Profile
13. Optimization Visualization
14. LLM Provider Console

P2（可后续）：
15. Scenario 管理
16. Metric Schema
17. Adapter 查看
```

---

## 最大风险

```
最大风险不是技术，而是 UI 做成"什么都能配"。

CheckpointAI 的 UI 应该逼你少操作：

系统告诉你：这里有 3 件事需要判断
你点进去：看到证据、风险、变化
你做决定：批准 / 拒绝 / 备注
系统记录：为什么这么决定
```
