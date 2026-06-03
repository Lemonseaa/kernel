# Architecture Overview
# checkpointAI Multi-Agent操作系统 - 完整架构

> Status: historical reference.
>
> This document captures the V0/V1 architecture when CheckpointAI was still framed as a general Multi-Agent OS.
> The current direction is defined in [BLUEPRINT.md](BLUEPRINT.md): CheckpointAI is now a code-first Agent experiment and optimization system, not a low-code Workflow Builder, Dify clone, or generic Agent Runtime.
> Keep this document for reusable ideas such as isolation, provider abstraction, policy, cost, and observability; do not treat it as the current product roadmap.

**版本：V1**
**日期：2026-06-02**

---

## 核心设计目标

1. **多业务线** — 每条业务线独立隔离，可创建/暂停/删除
2. **多模型适配** — 不绑定特定Provider，支持国内外主流模型
3. **高可扩展性** — 模块化设计，支持插件、模板、自定义

---

## 一、架构层次总览

```
┌─────────────────────────────────────────────────────────────────┐
│                          checkpointAI (组织层)                              │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐           │
│  │BusinessLine │  │BusinessLine │  │BusinessLine │  ...        │
│  │    网站     │  │   内容      │  │   电商      │           │
│  └─────────────┘  └─────────────┘  └─────────────┘           │
│         │                │                │                     │
│         └────────────────┼────────────────┘                     │
│                          │                                        │
│              ┌──────────┴──────────┐                           │
│              │    Shared Layer     │                           │
│              │  (共享基础设施)      │                           │
│              └──────────┬──────────┘                           │
│                         │                                        │
│              ┌──────────┴──────────┐                           │
│              │   LLM Abstraction  │                           │
│              │   (模型抽象层)       │                           │
│              └────────────────────┘                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## 二、多业务线架构

### 2.1 BusinessLine实体

每条业务线是完全独立的子系统：

```python
class BusinessLine:
    id: str
    name: str
    status: BusinessLineStatus  # ACTIVE/PAUSED/ARCHIVED
    
    agents: AgentRegistry      # 独立Agent
    context: ContextManager    # 独立上下文
    evaluation: EvaluationRunner # 独立评估
    workflows: WorkflowRegistry # 独立工作流
    
    config: BusinessLineConfig  # 独立配置
```

### 2.2 生命周期

```
CREATE → ACTIVE ←→ PAUSED → ARCHIVE → DELETE
```

| 状态 | 说明 |
|---|---|
| ACTIVE | 正常运行，可执行Run |
| PAUSED | 暂停，保留所有状态 |
| ARCHIVED | 归档，不显示在活跃列表 |
| DELETE | 彻底删除（不可逆） |

### 2.3 隔离与共享

| 资源 | 隔离级别 |
|---|---|
| Agent Registry | 完全隔离 |
| Context/Memory | 完全隔离 |
| Runs历史 | 完全隔离 |
| Workflow Templates | 完全隔离 |
| Provider | 共享 |
| Base Tools | 共享 |
| System Policies | 共享，可覆盖 |

### 2.4 跨业务线协作

```python
# 显式授权
bl_a.grant(bl_b.id, "website_writer_agent")

# 跨线调用
result = bl_b.run(using_agent="bl_a.website_writer_agent", ...)
```

---

## 三、多模型适配架构

### 3.1 设计原则

**不绑定任何Provider，所有交互通过抽象接口**

### 3.2 LLM抽象层

```
┌─────────────────────────────────────────┐
│          LLM Abstraction Layer           │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │      LLMProvider (抽象基类)       │   │
│  │                                 │   │
│  │  async chat(messages) -> str    │   │
│  │  async embeddings(text) -> list  │   │
│  │  async vision(images) -> str     │   │
│  │  get_capabilities() -> dict     │   │
│  │  get_pricing() -> PricingInfo   │   │
│  └─────────────────────────────────┘   │
│                   ▲                     │
│                   │ 实现                 │
│  ┌───────────────┼───────────────┐    │
│  │               │               │    │
│  ▼               ▼               ▼    │
│ MiniMax     OpenAI          Anthropic   │
│ Provider    Provider         Provider    │
│    │           │               │       │
│    └───────────┼───────────────┘       │
│                ▼                        │
│         其他Provider...                  │
└─────────────────────────────────────────┘
```

### 3.3 Provider接口定义

```python
class LLMProvider(ABC):
    """LLM Provider统一接口"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider名称"""
    
    @property
    def capabilities(self) -> ProviderCapabilities:
        """ Provider能力"""
        return ProviderCapabilities(
            streaming=True,
            vision=False,
            function_calling=True,
            max_context_tokens=128_000,
        )
    
    @abstractmethod
    async def chat(
        self,
        messages: list[ChatMessage],
        model: str = None,
        temperature: float = 0.7,
        max_tokens: int = None,
        **kwargs
    ) -> ChatResponse:
        """发送对话"""
        pass
    
    @abstractmethod
    async def embeddings(
        self,
        texts: list[str],
        model: str = None,
        **kwargs
    ) -> list[list[float]]:
        """获取文本向量"""
        pass
    
    @abstractmethod
    def get_token_count(self, text: str) -> int:
        """计算Token数（估算）"""
        pass
```

### 3.4 已支持/待支持的Provider

| Provider | 状态 | 说明 |
|---|---|---|
| MiniMax | ✓ 已实现 | 主力Provider |
| OpenAI | ✓ 已实现 | GPT系列 |
| Anthropic | 待实现 | Claude系列 |
| Google | 待实现 | Gemini系列 |
| Grok | 待实现 | xAI |
| SiliconFlow | 待实现 | 国内模型聚合 |
| Ollama | 待实现 | 本地模型 |
| Custom | 支持 | 用户自定义Provider |

### 3.5 模型路由器（可选）

```python
class ModelRouter:
    """根据任务类型自动选择最优模型"""
    
    def __init__(self, providers: dict[str, LLMProvider]):
        self.providers = providers
        self.rules = []
    
    def add_rule(self, condition: callable, provider: str, model: str):
        """添加路由规则"""
        self.rules.append((condition, provider, model))
    
    async def route(self, task: Task) -> tuple[str, str]:
        """返回(provider_name, model)"""
        for condition, provider, model in self.rules:
            if condition(task):
                return provider, model
        return "minimax", "MiniMax-Text-01"  # 默认

# 使用示例
router = ModelRouter(all_providers)
router.add_rule(
    lambda t: t.type == "code" and t.complexity > 7,
    "openai", "gpt-4-turbo"
)
router.add_rule(
    lambda t: t.type == "creative" and t.urgent,
    "minimax", "MiniMax-Text-01"
)
```

### 3.6 Token计费统一

```python
class PricingEngine:
    """统一计费引擎"""
    
    def __init__(self):
        self.pricing = {
            "minimax": PriceModel(
                input_per_1k=0.01,
                output_per_1k=0.03,
            ),
            "openai": PriceModel(
                input_per_1k=0.03,
                output_per_1k=0.06,
            ),
            # ...
        }
    
    def calculate_cost(
        self,
        provider: str,
        input_tokens: int,
        output_tokens: int
    ) -> CostBreakdown:
        price = self.pricing[provider]
        input_cost = (input_tokens / 1000) * price.input_per_1k
        output_cost = (output_tokens / 1000) * price.output_per_1k
        return CostBreakdown(
            provider=provider,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_cost=input_cost + output_cost
        )
```

---

## 四、高可扩展性架构

### 4.1 扩展点一览

```
┌─────────────────────────────────────────────────────────┐
│                    Extension Points                      │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │  Agent   │  │   Tool   │  │ Provider │             │
│  │ 插件      │  │  插件     │  │  插件     │             │
│  └──────────┘  └──────────┘  └──────────┘             │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │Workflow │  │Evaluation│  │Policy   │             │
│  │模板插件  │  │  插件     │  │  规则插件 │             │
│  └──────────┘  └──────────┘  └──────────┘             │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │Context  │  │Notifier │  │Storage  │             │
│  │存储插件  │  │  插件     │  │  后端插件 │             │
│  └──────────┘  └──────────┘  └──────────┘             │
└─────────────────────────────────────────────────────────┘
```

### 4.2 Agent插件

```python
class BaseAgent(ABC):
    """Agent基类，所有Agent必须实现"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def role(self) -> str:
        pass
    
    @abstractmethod
    async def execute(self, task: Task, context: Context) -> ExecutionResult:
        pass

# 注册插件
checkpoint_ai.plugins.register_agent(MyCustomAgent)
```

### 4.3 Tool插件

```python
class BaseTool(ABC):
    """Tool基类"""
    
    @property
    def name(self) -> str:
        pass
    
    @property
    def risk_level(self) -> RiskLevel:
        return RiskLevel.LOW  # LOW/MEDIUM/HIGH/CRITICAL
    
    @property
    def requires_approval(self) -> bool:
        return self.risk_level >= RiskLevel.HIGH
    
    @abstractmethod
    async def execute(self, params: dict) -> ToolResult:
        pass

# 工具风险分级
class RiskLevel(str, Enum):
    LOW = "low"           # 只读，无风险
    MEDIUM = "medium"     # 写入本地文件
    HIGH = "high"          # 修改外部系统
    CRITICAL = "critical" # 不可逆操作（删除/支付）
```

### 4.4 Provider插件

```python
# 接入新Provider只需实现接口
class CustomProvider(LLMProvider):
    async def chat(self, messages, **kwargs):
        # 调用自定义API
        pass
    
    async def embeddings(self, texts, **kwargs):
        pass
    
    def get_token_count(self, text):
        pass

# 注册
checkpoint_ai.providers.register("custom", CustomProvider(api_key="..."))
```

### 4.5 Evaluation插件

```python
class BaseEvaluator(ABC):
    """评估器基类"""
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @abstractmethod
    def evaluate(self, content: str, context: dict) -> EvaluationResult:
        pass

# 内置评估器
class ReadabilityEvaluator(BaseEvaluator):
    name = "readability"
    
class SEOEvaluator(BaseEvaluator):
    name = "seo_quality"

# 注册
checkpoint_ai.evaluation.register(MyCustomEvaluator)
```

### 4.6 Policy插件

```python
class PolicyRule(BaseModel):
    """策略规则"""
    
    id: str
    name: str
    
    # 匹配条件
    condition: PolicyCondition
    
    # 执行动作
    action: PolicyAction
    
    # 效果
    effect: PolicyEffect  # ALLOW / DENY / REQUIRE_APPROVAL

class PolicyCondition(BaseModel):
    """条件类型"""
    type: str  # "task_type" / "tool_name" / "risk_level" / "agent_role"
    operator: str  # "equals" / "contains" / "gt" / "lt"
    value: Any

# 示例规则
PolicyRule(
    id="high_risk_tool",
    name="高风险工具需要审批",
    condition=PolicyCondition(
        type="risk_level",
        operator="gte",
        value="HIGH"
    ),
    action=PolicyAction(type="require_approval"),
    effect=PolicyEffect.REQUIRE_APPROVAL
)
```

### 4.7 Storage插件

```python
class StorageBackend(ABC):
    """存储后端抽象"""
    
    @abstractmethod
    async def save(self, key: str, value: Any) -> bool:
        pass
    
    @abstractmethod
    async def load(self, key: str) -> Optional[Any]:
        pass
    
    @abstractmethod
    async def delete(self, key: str) -> bool:
        pass
    
    @abstractmethod
    async def list(self, prefix: str) -> list[str]:
        pass

# 内置后端
class SQLiteStorage(StorageBackend):
    """SQLite后端"""
    pass

class PostgresStorage(StorageBackend):
    """PostgreSQL后端"""
    pass

class S3Storage(StorageBackend):
    """S3后端"""
    pass
```

### 4.8 Notification插件

```python
class NotificationChannel(ABC):
    """通知渠道"""
    
    @property
    def name(self) -> str:
        pass
    
    @abstractmethod
    async def send(self, message: Notification) -> bool:
        pass

# 内置渠道
class ConsoleChannel(NotificationChannel):
    name = "console"
    async def send(self, message):
        print(f"[{message.type}] {message.title}")
        return True

class WebhookChannel(NotificationChannel):
    name = "webhook"
    # 支持Telegram/钉钉/飞书等

class EmailChannel(NotificationChannel):
    name = "email"
    # SMTP发送
```

### 4.9 插件注册机制

```python
class PluginRegistry:
    """插件注册表"""
    
    def __init__(self):
        self.agents = {}
        self.tools = {}
        self.providers = {}
        self.evaluators = {}
        self.policies = {}
        self.storages = {}
        self.notifiers = {}
    
    def register(self, plugin_type: str, name: str, plugin):
        """注册插件"""
        getattr(self, plugin_type)[name] = plugin
    
    def get(self, plugin_type: str, name: str):
        """获取插件"""
        return getattr(self, plugin_type).get(name)
    
    def list(self, plugin_type: str) -> list[str]:
        """列出所有插件"""
        return list(getattr(self, plugin_type).keys())
```

---

## 五、BusinessLine模板系统

### 5.1 模板类型

| 模板 | 用途 |
|---|---|
| BusinessLineTemplate | 创建新业务线 |
| WorkflowTemplate | 创建新工作流 |
| AgentTemplate | 创建新Agent |

### 5.2 BusinessLine模板

```python
class BusinessLineTemplate(BaseModel):
    """业务线模板"""
    
    id: str
    name: str
    description: str
    
    # 预设Agent
    agents: list[AgentTemplate] = []
    
    # 预设工具
    tools: list[str] = []  # 工具名称列表
    
    # 评估规则
    evaluation_rules: list[str] = []
    
    # 策略
    policies: list[PolicyRule] = []
    
    # 工作流
    workflows: list[WorkflowTemplate] = []

# 内置模板
TEMPLATES = {
    "website": BusinessLineTemplate(
        id="website",
        name="个人网站业务",
        agents=[
            AgentTemplate(name="designer", role="设计师"),
            AgentTemplate(name="developer", role="开发工程师"),
            AgentTemplate(name="reviewer", role="审核员"),
        ],
        tools=["file_write", "shell", "browser_screenshot"],
        evaluation_rules=["website_seo", "website_quality"],
        policies=[
            PolicyRule(id="publish_require_approval", action="publish", effect="REQUIRE_APPROVAL"),
        ],
    ),
    "content": BusinessLineTemplate(
        id="content",
        name="内容创作业务",
        agents=[
            AgentTemplate(name="researcher", role="选题研究员"),
            AgentTemplate(name="writer", role="文案撰写"),
            AgentTemplate(name="editor", role="内容编辑"),
        ],
        tools=["web_search", "file_write"],
        evaluation_rules=["readability", "seo_quality", "originality"],
    ),
    "blank": BusinessLineTemplate(
        id="blank",
        name="空白业务线",
        agents=[],
        tools=[],
        evaluation_rules=[],
        policies=[],
    ),
}
```

### 5.3 创建业务线

```python
# 从模板创建
bl = checkpoint_ai.create_business_line(
    name="客户A的网站",
    template="website"
)

# 从空白创建
bl = checkpoint_ai.create_business_line(
    name="新业务",
    template="blank"
)

# 克隆已有业务线
bl = checkpoint_ai.create_business_line(
    name="基于A业务的B业务",
    clone_from=bl_a.id
)
```

---

## 六、数据流总览

### 6.1 请求处理流程

```
User Request
    │
    ▼
Hub (路由)
    │
    ▼
BusinessLine
    │
    ├──► PolicyEngine (权限检查)
    │
    ├──► WorkflowEngine (编排)
    │         │
    │         ├──► Agent Selection
    │         │
    │         ├──► LLM Provider (路由到具体Provider)
    │         │
    │         ├──► Tool Call
    │         │
    │         ├──► Evaluation Gate
    │         │
    │         └──► Human Gate (if needed)
    │
    ├──► Context Update
    │
    ├──► Artifact Created
    │
    └──► Event Published
```

### 6.2 事件流

```
Task Started
    │
    ▼
LLM Call ──────────────► Token Counter
    │                         │
    │◄────────────────────────┘
    │
    ▼
Tool Call ─────────────► Tool Registry
    │                         │
    │                         ▼
    │◄────────────────────────┘
    │
    ▼
Evaluation
    │
    ├──► Pass ────► Task Completed
    │
    └──► Fail ────► Human Gate (Notification)
                          │
                          ▼
                     Approved/Rejected
                          │
                          ▼
                     Task Completed/Rejected
```

---

## 七、相关文档

| 文档 | 内容 |
|---|---|
| BUSINESS_LINE_ARCHITECTURE.md | 多业务线详细设计 |
| DESIGN_PRINCIPLES.md | 设计原则（创新如何自然发生） |
| INNOVATION_RESEARCH.md | 业界创新点迁移研究 |
