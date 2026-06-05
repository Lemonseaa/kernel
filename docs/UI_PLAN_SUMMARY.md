# CheckpointAI Web UI 规划总结

## 背景

CheckpointAI V1-V6已完成，当前Web UI有基础功能：
- Dashboard / Runs / Reports / Shadows / Backup / Scenarios / Adapters / Approvals / Autonomy

下一阶段目标：最大化人和AI的协作能力。

---

## UI布局

```
┌─────────────────────────────────────────────────────────────┐
│                           Header                            │
├───────────────┬───────────────────────────────────────────┤
│               │                                           │
│   看板层     │                                           │
│   Dashboard  │                                           │
│   Runs       │            Hermes                          │
│   Reports    │         （右悬浮对话框）                  │
│   Shadows    │                                           │
│   Backup     │      点出来对话                           │
│   Insights   │      帮你理解                             │
│   Scheduler  │      记忆偏好                           │
│   Decision   │      代理修改                             │
│   Events     │                                           │
│   Alerts     │                                           │
│               ├───────────────────────────────────────────┤
│   业务层     │                                           │
│   业务分区   │                                           │
│     ├Workflow│                                           │
│     ├Agent   │                                           │
│     ├Adapter │                                           │
│     ├Scenarios│                                          │
│     ├Templates│                                           │
│     ├Tools   │                                           │
│     ├LLM     │                                           │
│     ├Autonomy│                                           │
├───────────────┤                                           │
│   审批层     │                                           │
│   Approval    │                                           │
│               │                                           │
├───────────────┤                                           │
│   设置层     │                                           │
│   Memory     │                                           │
│   偏好      │                                           │
└───────────────┴───────────────────────────────────────────┘
```

---

## 四大层

### 1. 看板层

```
功能：看系统状态、做操作、查历史

页面：
- Dashboard - 系统总览
- Runs - 运行历史/触发
- Reports - 报告
- Shadows - Shadow对比
- Backup - 备份管理
- Insights - 跨场景洞察
- Scheduler - 调度任务
- Decision - 决策日志
- Events - 事件审计
- Alerts - 告警配置
- Notifications - 通知设置
- Diagnostics - 诊断
```

### 2. 业务层

```
功能：构建业务、构建agent、配置系统

页面：业务分区

业务分区内容：
- 不同业务线分开管理
- 每个业务线有自己的scenario/adapter/config
- Workflow可视化：人只读，Hermes可改
- 构建Agent：人描述需求，Hermes生成配置
- Adapter - Adapter列表/配置
- Scenarios - 场景管理
- Templates - 模板管理
- Tools - 工具管理
- LLM - 模型配置
- Autonomy - 自治队列
```

### 3. 审批层

```
功能：审批proposal

页面：
- Approval Inbox
```

### 4. 设置层

```
功能：用户偏好、记忆

页面：
- User Profile - 人类正式偏好
- Suggested Profile Notes - Hermes建议草稿
- 偏好设置
```

---

## Hermes

### 定位

```
- 不是外部工具
- 就是系统的一部分
- 专属AI助手，在UI里对话
- 可选，没有也能跑
```

### 三个角色

```
1. 你的手
   - 帮你做代码级别的改动
   - 修改prompt
   - 配置agent
   - 但都走proposal流程

2. 你的记忆
   - 帮人总结审美、偏好、风格
   - 生成建议草稿
   - 不自动写入正式偏好

3. 你的老师
   - 帮不懂的人看懂系统在干什么
   - 汇总复杂信息
```

### 能力

```
- 查看所有内容
- 代码修改代理
- 审批辅助理解
- 构建Agent辅助
- 总结偏好建议草稿
- Workflow修改（走proposal）
```

### 安全边界

```
- 工作路径限定在系统文件内
- 不能删除数据
- 不能直接部署
- 所有修改走proposal/shadow/approval
- 不能直接修改 `user/USER_PROFILE.md`
```

---

## UI和Hermes的关系

```
UI = 人直接操作
Hermes = 对话辅助

人可以选择：
1. 自己看、自己操作
2. 让Hermes帮忙，然后走审批流程

Hermes不能替代：
1. 人审批
2. 人对正式偏好的定义权
3. Workflow直接修改（必须走proposal）
```

---

## User Profile / 人类偏好

详细规划见 `docs/USER_PREFERENCE_PLAN.md`。

```
user/
├── USER_PROFILE.md
└── SUGGESTED_PROFILE_NOTES.md
```

定位：

```
USER_PROFILE.md = 人的长期原则，人手写，Agent只读
SUGGESTED_PROFILE_NOTES.md = Hermes建议草稿，不能作为正式约束
```

流程：

```
DecisionLog / Approval comments / Validation summaries / Safety findings / 历史对话
        ↓
Hermes 总结
        ↓
SUGGESTED_PROFILE_NOTES.md
        ↓
人查看、修改、复制
        ↓
人手动写入 USER_PROFILE.md
```

硬规则：

```
1. Hermes 可以读正式偏好
2. Hermes 可以生成偏好建议
3. Hermes 不可以直接修改正式偏好
4. Agent 不可以修改正式偏好
5. USER_PROFILE.md 是正式偏好唯一来源
6. SUGGESTED_PROFILE_NOTES.md 不能作为正式约束
7. 所有 profile 保存必须产生 diff 和 DecisionLog
```

---

## Agent配置弹窗

```
业务层 → Agent配置弹窗
              ↓
        点击"配置"按钮

配置内容：
- 技能列表
- MCP servers
- 触发条件
- 约束规则
- LLM模型

和Hermes无关，独立弹窗
```

---

## Workflow可视化

```
位置：业务层

功能：
- 人只读，看到agent协作过程
- 不能直接改，必须通过Hermes
- Hermes可以改（走proposal流程）
```

---

## 版本分支机制

```
位置：业务层

人的操作：
- [锁定当前配置] - 点击即锁定
- [创建新分支] - 点击即创建
- [切换版本] - 选择即切换
- [回滚] - 选择即回滚

Hermes也可以：
- "帮我锁定这个配置"
- "开一个新分支"

锁定后：
- 配置变成只读
- Agent不能自动改这个参数
- 除非开新分支解锁
```

---

## 三大系统并行

```
系统1：CheckpointAI（V1-V6）
- 记录、优化、审批
- 现有功能

系统2：内置优化系统
- Observer/Proposer/Validator/SafetyMonitor
- 自动发现问题、生成建议、验证
- CrewAI 可作为实现选项，但不是核心依赖

系统3：Hermes
- 可选对话界面
- 和前两个都交互
- 但不是必须的
```

---

## UI现状和计划

### 已有

```
✅ Dashboard
✅ Runs
✅ Reports
✅ Shadows
✅ Backup
✅ Scenarios
✅ Adapters
✅ Approvals
✅ Autonomy
```

### 待做

```
❌ Insights - 跨场景洞察
❌ Scheduler - 调度任务
❌ Decision - 决策日志
❌ Events - 事件审计
❌ Alerts - 告警配置
❌ Hermes - 对话界面
❌ Workflow可视化
❌ 构建Agent界面
❌ 业务分区
❌ User Profile / Suggested Notes
❌ Memory/偏好设置
```

---

## 执行顺序

```
Phase 1：Learning Loop Console
  - Observations
  - Proposals
  - Validations
  - Safety

Phase 2：Config Version / Branch
  - Lock
  - Branch
  - Switch
  - Rollback

Phase 3：Business Line Workspace
  - BusinessLine管理
  - Scenarios
  - External Agents

Phase 4：Agent Config
  - Skills
  - Tools
  - MCP Servers
  - Triggers
  - Constraints
  - Model

Phase 5：Workflow可视化
  - 只读展示 Learning Flow
  - 修改必须走proposal，可由Hermes或UI表单生成proposal

Phase 6：Ops Console
  - Decision/Events
  - Alerts
  - Diagnostics
  - Scheduler

Phase 7：User Profile / Preference
  - USER_PROFILE.md 编辑
  - SUGGESTED_PROFILE_NOTES.md 查看
  - 保存diff和DecisionLog

Phase 8：Hermes
  - 右悬浮对话框
  - 解释当前页面
  - 总结proposal
  - 生成偏好建议草稿
  - 生成proposal但不直接执行
```

---

## 原则

```
1. Hermes是增强，不是替代
   - 没有也能跑

2. Workflow人不能直接改
   - 必须走proposal
   - proposal可以由Hermes生成，也可以由UI表单生成

3. 配置弹窗独立
   - 和Hermes无关

4. 版本分支有独立按钮
   - 锁定/分支/切换/回滚

5. 人类偏好由人定义
   - Hermes只生成建议草稿
   - Agent只读取正式profile
```
