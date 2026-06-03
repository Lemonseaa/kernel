# Business Line Architecture
# 多业务线checkpointAI系统的架构设计

> Status: historical reference.
>
> This document captures the old BusinessLine-first architecture. The current source of truth is [BLUEPRINT.md](BLUEPRINT.md).
> The useful part that remains is scenario/business-domain isolation: quant research, media growth, and other domains must not pollute each other.
> Do not read this as a mandate to build a full generic business-line runtime, workflow builder, or enterprise tenant system.

**版本：V1**
**日期：2026-06-02**

---

## 1. 核心理念

### 1.1 什么是BusinessLine

BusinessLine（业务线）是checkpointAI系统的第一等公民。

不是"加一个tenant_id字段"，是重新组织系统的核心抽象层次。

每个业务线是一个完整的、独立的、可以独立运转的子系统。

---

### 1.2 业务线不是什么

- 不是"标签"：业务线有完整的生命周期
- 不是"配置"：业务线有独立的资源和状态
- 不是"命名空间"：业务线之间不只是隔离，还有协作

---

### 1.3 为什么需要BusinessLine

checkpointAI的场景：
- 同时运营多条业务线（网站/内容/电商/客服...）
- 每条业务线有不同的Agent配置
- 每条业务线有不同的评估标准
- 每条业务线有不同的工具集
- 业务线之间可能需要共享资源

---

## 2. 架构层次

### 2.1 完整层次结构

```
checkpointAI (组织层)
│
├── Shared Infrastructure (共享基础设施)
│   ├── LLM Providers (MiniMax / OpenAI / ...)
│   ├── Base Tools (文件读写/Shell/搜索/...)
│   ├── System Policies (全局安全策略)
│   └── System Templates (通用模板)
│
├── BusinessLine A (业务线)
│   ├── BusinessLine Config
│   │   ├── name
│   │   ├── status
│   │   ├── evaluation_rules
│   │   └── policies
│   │
│   ├── Agents (业务专属Agent)
│   │   ├── website_writer
│   │   ├── seo_optimizer
│   │   └── content_reviewer
│   │
│   ├── Workflow Templates (业务专属模板)
│   │   ├── website_flow
│   │   └── blog_flow
│   │
│   ├── Evaluation Rules (业务专属评估)
│   │   ├── website_quality
│   │   └── seo_score
│   │
│   ├── Context (业务专属记忆)
│   │   ├── project_memory
│   │   └── client_preferences
│   │
│   └── Runs (历史执行记录)
│       ├── run_001
│       └── run_002
│
├── BusinessLine B (业务线)
│   └── ...
│
└── Hub (调度与聚合)
    ├── Cross-BusinessLine Workflow
    ├── Resource Scheduling
    └── Global Monitoring
```

---

### 2.2 层次职责

| 层次 | 职责 | 隔离性 |
|---|---|---|
| checkpointAI层 | 组织管理、全局监控、跨业务线协调 | N/A |
| Shared层 | 基础资源、Provider、工具、全局策略 | 共享，但可配置 |
| BusinessLine层 | 业务执行、Agent、模板、评估 | 完全隔离 |
| Hub层 | 跨业务线编排、统一入口 | 协调层 |

---

## 3. BusinessLine实体

### 3.1 BusinessLine模型

```python
class BusinessLine(BaseModel):
    """业务线核心实体"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str  # 业务线名称，如"个人网站业务"
    
    status: BusinessLineStatus = BusinessLineStatus.ACTIVE
    
    # 业务配置
    config: BusinessLineConfig
    
    # 创建时间
    created_at: float = Field(default_factory=time.time)
    
    # 最后活跃时间
    last_active_at: float = Field(default_factory=time.time)

class BusinessLineStatus(str, Enum):
    ACTIVE = "active"      # 运行中
    PAUSED = "paused"      # 暂停，保留状态
    ARCHIVED = "archived" # 归档，不再运行
    DELETED = "deleted"   # 已删除

class BusinessLineConfig(BaseModel):
    """业务线配置"""
    
    # 评估规则
    evaluation_rules: list[str] = []  # 评估规则ID列表
    
    # Policy覆盖
    policy_overrides: dict[str, PolicyRule] = {}
    
    # 资源限制
    resource_limits: ResourceLimits = ResourceLimits()
    
    # 通知配置
    notification_channels: list[str] = []  # 渠道ID列表

class ResourceLimits(BaseModel):
    """资源限制"""
    
    max_concurrent_runs: int = 10
    max_agents: int = 50
    max_token_per_day: int = 1_000_000
    max_storage_mb: int = 1000
```

---

### 3.2 BusinessLine生命周期

```
创建(CREATE)
    │
    ▼
活跃(ACTIVE) ←───────→ 暂停(PAUSED)
    │                      │
    │                      │ (用户暂停)
    │                      ▼
    │                   继续(RESUME)
    │                      │
    │◄─────────────────────┘
    │
    ▼
归档(ARCHIVE)
    │
    ▼
删除(DELETE)
```

| 操作 | 行为 |
|---|---|
| CREATE | 分配隔离空间 + 初始化 + 可选模板填充 |
| PAUSE | 停止新Run + 保留所有状态 |
| RESUME | 恢复运行 |
| ARCHIVE | 停止运行 + 保留数据 + 不显示在活跃列表 |
| DELETE | 删除所有资源（不可逆） |

---

### 3.3 BusinessLine创建

```python
# 方式1：从模板创建
bl = checkpoint_ai.create_business_line(
    name="个人网站业务",
    template="website",  # 预设模板
    config=BusinessLineConfig(
        evaluation_rules=["website_seo", "website_quality"]
    )
)

# 方式2：从已有业务线克隆
bl = checkpoint_ai.create_business_line(
    name="网站业务v2",
    clone_from="business_line_id",  # 克隆配置
    config={...}
)

# 方式3：空白创建
bl = checkpoint_ai.create_business_line(
    name="新业务",
    template=None,  # 空白
)
```

---

## 4. 隔离与共享模型

### 4.1 隔离原则

BusinessLine之间默认完全隔离：

| 资源 | 隔离级别 | 说明 |
|---|---|---|
| Agent Registry | 完全隔离 | A看不到B的Agent |
| Context | 完全隔离 | A看不到B的记忆 |
| Runs | 完全隔离 | A看不到B的执行记录 |
| Workflow Templates | 完全隔离 | A看不到B的模板 |
| Evaluation Rules | 可继承 | 可继承Shared层，也可自己定义 |
| Policy | 可覆盖 | 可覆盖Shared层策略 |

---

### 4.2 共享原则

Shared层资源可跨BusinessLine使用：

```python
# Shared层的Provider
checkpoint_ai.shared.providers  # 所有Provider

# Shared层的Base Tools
checkpoint_ai.shared.tools  # 文件读写、Shell等基础工具

# BusinessLine可引用Shared资源
bl.add_tool(checkpoint_ai.shared.tools["file_write"])
bl.add_tool(checkpoint_ai.shared.tools["http_request"])
```

---

### 4.3 跨BusinessLine协作

需要显式授权：

```python
# BusinessLine A授权给BusinessLine B使用其Agent
bl_a.grant(bl_b.id, "website_writer_agent")

# BusinessLine B跨线调用
bl_b.run(using_agent="bl_a.website_writer_agent", ...)
```

---

## 5. 模板系统

### 5.1 模板类型

| 模板类型 | 用途 |
|---|---|
| BusinessLine模板 | 创建新业务线 |
| Workflow模板 | 创建新Workflow |
| Agent模板 | 创建新Agent |

---

### 5.2 BusinessLine模板

```python
# 模板定义
template_website = BusinessLineTemplate(
    id="website",
    name="个人网站业务",
    
    # 默认Agent
    agents=[
        AgentTemplate(name="designer", role="设计师"),
        AgentTemplate(name="developer", role="开发工程师"),
        AgentTemplate(name="reviewer", role="审核员"),
    ],
    
    # 默认工具
    tools=["file_write", "shell", "browser_screenshot"],
    
    # 默认评估规则
    evaluation_rules=["website_seo", "website_quality", "accessibility"],
    
    # 默认Policy
    policies=[
        PolicyRule(action="publish", effect="require_approval"),  # 发布需要审批
        PolicyRule(action="deploy", effect="require_approval"),
    ],
    
    # 默认工作流
    workflows=[
        WorkflowTemplate(id="website_create", steps=[...]),
        WorkflowTemplate(id="website_update", steps=[...]),
    ],
)

# 使用模板创建
bl = checkpoint_ai.create_business_line(name="客户A的网站", template="website")
```

---

### 5.3 Workflow模板

```python
workflow_template = WorkflowTemplate(
    id="website_create",
    name="网站创建流程",
    
    steps=[
        Step(id="1", agent="designer", task="设计网站原型"),
        Step(id="2", agent="developer", task="开发网站", depends_on=["1"]),
        Step(id="3", agent="reviewer", task="审核代码", depends_on=["2"]),
        Step(id="4", agent="developer", task="部署上线", depends_on=["3"], requires_approval=True),
    ],
    
    # 评估节点
    evaluation_gates=[
        EvaluationGate(after_step="2", rules=["website_quality"]),
        EvaluationGate(after_step="4", rules=["website_seo", "accessibility"]),
    ],
)
```

---

## 6. 资源管理

### 6.1 BusinessLine资源限制

每个BusinessLine有独立的资源配额：

```python
class ResourceQuota(BaseModel):
    """资源配额"""
    
    max_concurrent_runs: int      # 最大并发Run数
    max_agents: int               # 最大Agent数
    max_token_per_day: int        # 每日Token上限
    max_storage_mb: int           # 存储上限(MB)
    max_cost_per_month: float     # 每月成本上限
```

---

### 6.2 资源调度

```
Hub资源调度
│
├── 按BusinessLine优先级分配
│   ├── 高优先级 → 保证资源
│   └── 低优先级 → 空闲资源
│
├── 共享资源池
│   ├── Provider调用
│   └── 基础工具
│
└── 隔离资源
    ├── BusinessLine专属Agent
    └── BusinessLine专属Context
```

---

## 7. 权限模型

### 7.1 权限层级

```
User (用户)
    │
    ▼
checkpointAI Admin (系统管理员)
    │ - 管理所有BusinessLine
    │ - 创建/删除BusinessLine
    │ - 修改Shared层配置
    │
    ▼
BusinessLine Admin (业务线管理员)
    │ - 管理单个BusinessLine
    │ - 创建/删除Agent
    │ - 修改业务配置
    │
    ▼
BusinessLine Operator (操作员)
    │ - 执行Run
    │ - 查看执行记录
    │ - 审批/拒绝
    │
    ▼
BusinessLine Viewer (观察者)
    - 只读权限
```

---

### 7.2 权限矩阵

| 操作 | Admin | BL Admin | Operator | Viewer |
|---|---|---|---|---|
| 创建BusinessLine | ✓ | ✗ | ✗ | ✗ |
| 删除BusinessLine | ✓ | ✗ | ✗ | ✗ |
| 创建Agent | ✓ | ✓ | ✗ | ✗ |
| 执行Run | ✓ | ✓ | ✓ | ✗ |
| 审批任务 | ✓ | ✓ | ✓ | ✗ |
| 查看日志 | ✓ | ✓ | ✓ | ✓ |
| 修改Policy | ✓ | ✓ | ✗ | ✗ |

---

## 8. 数据流

### 8.1 Run执行流程

```
User Request
    │
    ▼
Hub (路由到BusinessLine)
    │
    ▼
BusinessLine.AgentRegistry (选择Agent)
    │
    ▼
WorkflowEngine (编排Task)
    │
    ├──► PolicyEngine (权限检查)
    │
    ├──► EvaluationGate (质量检查)
    │
    ├──► HumanGate (需要审批?)
    │         │
    │         ▼
    │     Notification (推送给审批者)
    │         │
    │         ▼
    │     Wait for approval...
    │
    ├──► LLM Provider (执行)
    │
    ├──► ToolCall (工具调用)
    │
    ├──► Context (更新记忆)
    │
    └──► Artifact (产出)
            │
            ▼
        EventBus (发布事件)
            │
            ▼
        AuditLog (记录)
            │
            ▼
        Run State (保存)
```

---

### 8.2 跨BusinessLine流程

```
BusinessLine A                    Hub                     BusinessLine B
    │                              │                           │
    │  request_collaboration()     │                           │
    │────────────────────────────►│                           │
    │                              │                           │
    │  grant_resource()            │                           │
    │◄────────────────────────────│                           │
    │                              │                           │
    │                              │  delegate_task()           │
    │                              │───────────────────────────►│
    │                              │                           │
    │                              │  task_result              │
    │                              │◄─────────────────────────│
    │                              │                           │
    │  receive_result()            │                           │
    │◄────────────────────────────│                           │
```

---

## 9. 实现路径

### 9.1 V1：当前架构 + BusinessLine核心

目标：支持多BusinessLine，共享层未实现

```
变更：
- 新增 BusinessLine 模型
- 新增 BusinessLineRegistry
- Agent/Context/Run 加 business_line_id
- CheckpointAI 加 create_business_line()
- BusinessLine 有独立的 Registry 和 Context
```

### 9.2 V2：共享层 + Policy

目标：实现Shared层和Policy系统

```
变更：
- 新增 Shared 层
- Provider/Tool 可注册到 Shared
- PolicyEngine 实现继承/覆盖
- 跨BusinessLine授权机制
```

### 9.3 V3：模板系统 + 高级功能

目标：完整的模板和生命周期管理

```
变更：
- BusinessLineTemplate
- WorkflowTemplate
- AgentTemplate
- BusinessLine 克隆
- Archive/Delete 完整实现
```

---

## 10. 核心接口

### 10.1 CheckpointAI层接口

```python
class CheckpointAI:
    """checkpointAI CheckpointAI"""
    
    # BusinessLine管理
    def create_business_line(
        self,
        name: str,
        template: str = None,
        config: BusinessLineConfig = None,
    ) -> BusinessLine:
        """创建业务线"""
    
    def get_business_line(self, bl_id: str) -> BusinessLine:
        """获取业务线"""
    
    def list_business_lines(self, status: BusinessLineStatus = None) -> list[BusinessLine]:
        """列出业务线"""
    
    def delete_business_line(self, bl_id: str):
        """删除业务线"""
    
    @property
    def shared(self) -> SharedInfrastructure:
        """访问共享基础设施"""
```

### 10.2 BusinessLine层接口

```python
class BusinessLine:
    """业务线"""
    
    @property
    def agents(self) -> AgentRegistry:
        """业务专属Agent注册表"""
    
    @property
    def context(self) -> ContextManager:
        """业务专属上下文"""
    
    @property
    def evaluation(self) -> EvaluationRunner:
        """业务专属评估"""
    
    def create_run(self, workflow_id: str, input_data: dict) -> Run:
        """创建Run"""
    
    def grant(self, other_bl_id: str, resource_id: str):
        """授权给其他业务线"""
    
    def revoke(self, other_bl_id: str, resource_id: str):
        """撤销授权"""
```

---

## 11. 关键设计决策

### 11.1 为什么BusinessLine是第一等公民

因为业务线有独立的：
- 生命周期（创建/暂停/删除）
- 资源配额
- 配置和策略
- 执行上下文

如果只是加一个tenant_id，无法表达这些语义。

---

### 11.2 为什么共享层是显式的

因为在checkpointAI场景下：
- 有些资源（Provider）是所有业务线共用的
- 有些资源（业务专属Agent）是业务线私有的
- 必须显式区分，否则权限无法管理

---

### 11.3 为什么用模板而不是配置继承

因为：
- 模板可以版本化
- 模板可以预验证
- 模板可以社区共享
- 配置继承会导致隐式依赖，难以追踪

---

## 12. 未解决的问题

| 问题 | 状态 |
|---|---|
| 跨BusinessLine的事务一致性 | 待定 |
| BusinessLine之间的资源抢占 | 待定 |
| 业务线合并/拆分 | 未来需求 |
| BusinessLine的配额调整 | 运行时可调整 |

---

## 13. 相关文档

- [ARCHITECTURE.md](./ARCHITECTURE.md) - 基础架构
- [DESIGN_PRINCIPLES.md](./DESIGN_PRINCIPLES.md) - 设计原则
- [INNOVATION_RESEARCH.md](./INNOVATION_RESEARCH.md) - 创新研究
