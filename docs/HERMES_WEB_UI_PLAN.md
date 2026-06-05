# Hermes Web UI Plan

## 背景

CheckpointAI现有系统能记录和优化AI输出，但人和AI的协作能力还不够。

下一阶段目标：最大化人和AI的潜力。

---

## UI完整布局

```
┌─────────────────────────────────────────────────────────────┐
│                           Header                            │
├───────────────┬─────────────────────────────────────────────┤
│               │                                             │
│   看板层     │                                             │
│   Dashboard  │                                             │
│   Runs      │                                             │
│   Reports    │                                             │
│   Shadows    │            Hermes                            │
│   Backup     │         （右悬浮对话框）                     │
│   Insights   │                                             │
│   Scheduler  │      点出来对话                           │
│   Decision   │      帮你理解                             │
│   Events     │      记忆偏好                             │
│   Alerts     │      代理修改                             │
│               ├─────────────────────────────────────────────┤
│   业务层     │                                             │
│   业务分区   │                                             │
│     ├Workflow│      点出来对话                           │
│     ├Agent  │      帮你理解                             │
│     ├Adapter│      记忆偏好                             │
│     ├Scenarios│     代理修改                             │
│     ├Templates│                                            │
│     ├Tools  │                                             │
│     ├LLM    │                                             │
│     ├Autonomy│                                            │
├───────────────┤                                             │
│   审批层     │                                             │
│   Approval    │                                             │
│               │                                             │
├───────────────┤                                             │
│   设置层     │                                             │
│   Memory     │                                             │
│   User.md   │                                             │
│   偏好      │                                             │
└───────────────┴─────────────────────────────────────────────┘
```

---

## 四大层

### 1. 看板层

功能：看系统状态、做操作、查历史

页面：
```
Dashboard - 系统总览
Runs - 运行历史/触发
Reports - 报告
Shadows - Shadow对比
Backup - 备份管理
Insights - 跨场景洞察
Scheduler - 调度任务
Decision - 决策日志
Events - 事件审计
Alerts - 告警配置
Notifications - 通知设置
Diagnostics - 诊断
```

### 2. 业务层

功能：构建业务、构建agent、配置系统

页面：
```
业务分区 - 不同业务线分开管理
  ├Workflow - 工作流可视化（人只读，Hermes可改）
  ├Agent - 构建agent（人描述需求，Hermes生成配置）
  ├Adapter - Adapter列表/配置
  ├Scenarios - 场景管理
  ├Templates - 模板管理
  ├Tools - 工具管理
  ├LLM - 模型配置
  └Autonomy - 自治队列
```

### 3. 审批层

功能：审批proposal

页面：
```
Approval Inbox
```

### 4. 设置层

功能：用户偏好、记忆

页面：
```
Memory - 用户偏好/记忆
User.md - 用户档案
偏好设置
```

---

## Hermes（核心新增）

### 定位

```
不是外部工具
就是系统的一部分
专属AI助手，在UI里对话
```

### 三个角色

```
1. 你的手
   - 帮你做代码级别的改动
   - 修改prompt
   - 配置agent
   - 但都走proposal流程

2. 你的记忆
   - 记住你的审美、偏好、风格
   - 跨会话学习
   - 不需要每次重复解释

3. 你的老师
   - 帮不懂的人看懂系统在干什么
   - 汇总复杂信息
   - 用人能理解的语言解释
```

### 能力

```
1. 查看所有内容
   - 所有四层的内容都可以看

2. 代码修改
   - 帮人改prompt
   - 帮人调agent配置
   - 提交proposal

3. 审批辅助
   - 解释proposal改了什么
   - 提供背景信息
   - 但不替代人审批

4. 构建Agent辅助
   - 帮人描述想要的agent
   - Hermes帮生成配置

5. 记忆偏好
   - 记住用户风格
   - 基于偏好给建议

6. Workflow修改
   - 人不能直接改Workflow
   - Hermes可以改（走proposal流程）
```

### 安全边界

```
- 工作路径限定在系统文件内
- 不能删除数据
- 不能直接部署
- 所有修改走proposal/shadow/approval
```

---

## 权限设计

```
人：可以看所有
    可以通过Hermes修改Workflow/Agent
    不能直接改Workflow/Agent
    最终审批权在人

Hermes：可以看所有
       可以代理修改（走proposal流程）
       可以记忆偏好

Approval：独立模块
        Hermes可以看
        人自己决定批不批
```

---

## 技术实现

```
Backend：FastAPI（现有）
Frontend：React + Vite（现有）
Hermes模型：MiniMax（现有订阅）
偏好存储：SQLite / 文件
对话历史：存储供Hermes上下文用
```

---

## 执行顺序

```
Phase 1：Hermes对话界面
  - 右悬浮对话框
  - 基础对话
  - 记忆偏好

Phase 2：Hermes审批辅助
  - 查看Approval内容
  - 解释proposal

Phase 3：Hermes代码修改
  - 生成proposal
  - 走现有审批流程

Phase 4：Workflow可视化
  - 只读展示
  - Hermes可改

Phase 5：构建Agent界面
  - 人描述需求
  - Hermes生成配置

Phase 6：业务分区完整化
  - BusinessLine管理
  - Adapter配置
  - Scenarios配置
  - Templates/Tools/LLM配置

Phase 7：看板层完整化
  - Scheduler可视化
  - Decision/Events查看
  - Alerts/Notifications配置

Phase 8：设置层
  - Memory偏好
  - User.md档案
```

---

## 不做的事

```
- Hermes不替代人审批
- Workflow不能人直接改
- 不开放外部AI直接访问
- 不做复杂的权限系统
```
