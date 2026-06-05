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
V5.8 已实现：
- Bearer Token 保护的 console API
- Dashboard snapshot
- Approval list/detail/approve/reject
- Run list/detail/trigger
- Backup list/create/restore
- Scenario list/show/archive
- Adapter capability list
- Health endpoint

暂未实现：
- Shadow 专用 API
- Reports 专用 API
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
Charts: Recharts
Tables: TanStack Table
```

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

P2（可后续）：
10. Scenario 管理
11. Metric Schema
12. Adapter 查看
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
