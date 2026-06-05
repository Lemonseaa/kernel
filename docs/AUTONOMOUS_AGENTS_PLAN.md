# Autonomous Agents Architecture - Final Summary

> 讨论稿：这份文档保留 Hermes 对内置 Agent 的早期总结。正式 V7 命名采用 Observer / Proposer / Validator / SafetyMonitor，详见 `docs/V7_PLAN.md`。

## 目标

让CheckpointAI成为真正自动运转的优化系统，人只需要：
- 通过Hermes了解进度
- 手动修改配置
- 极少数高风险情况介入

---

## 核心架构

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│   Discovery → Monitor → Proposer → Refiner                 │
│       ↑                           ↓                         │
│       └───────── Knowledge ← ─── ┘                         │
│                                                             │
│   Safety Agent (监控执行、处理回滚)                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 5个Agent

### 1. Discovery Agent（发现者）

```
职责：主动找优化机会
触发：持续探索，不等异常
LLM：小型快速模型（高频执行）

主动发现：
- 哪些参数还有优化空间
- 历史数据里有什么模式
- 可以尝试的新方向
```

### 2. Monitor Agent（监控者）

```
职责：监控数据、发现异常
触发：定时检查 + 阈值触发
LLM：小型快速模型（高频执行）

监控内容：
- 指标变化
- 异常模式
- 性能下降
```

### 3. Proposer Agent（建议者）

```
职责：分析原因、生成建议
触发：Monitor发现异常 / Discovery找到机会
LLM：大型推理模型（需要分析能力）

生成内容：
- 具体的改动建议
- 预期效果
- 风险评估
- 建议参数值
```

### 4. Refiner Agent（优化者）

```
职责：执行改动、验证效果、更新知识
触发：Proposal批准后
LLM：中型稳定模型

执行流程：
- 执行proposal
- 运行测试
- 验证效果
- 记录到知识库
```

### 5. Safety Agent（安全员）

```
职责：监控执行、处理紧急回滚
触发：持续监控
LLM：小型快速模型

职责：
- 监控执行结果
- 发现问题触发回滚
- 记录失败模式
- 防止连锁故障
```

---

## Knowledge Base（知识库）

```
存储：
- 历史成功的proposal
- 历史失败的proposal
- 成功参数组合
- 失败原因模式

支持：
- Discovery寻找机会
- Monitor发现异常
- Proposer生成建议
```

---

## Hermes的角色

```
定位：可选的对话界面

作用：
- 人问Hermes了解系统状态
- Hermes读取上下文回答问题
- 记忆人的偏好

重要性：
- 没有Hermes系统照样跑
- Hermes只是增强体验
- 不是核心功能
```

---

## 自动循环流程

```
1. Discovery持续探索
   ↓ 找到优化机会
2. Monitor监控数据
   ↓ 发现异常
3. Proposer分析原因
   ↓ 生成建议
4. Refiner执行验证
   ↓ 成功
5. 更新Knowledge
   ↓
6. 回到1（持续循环）
```

---

## 风险分级

```
低风险（自动执行）：
- 小参数微调
- 经过多次验证的改动
- 预期效果明确

中风险（通知确认）：
- 中等幅度改动
- 新方向尝试
- Hermes通知人，人说"知道了"

高风险（必须审批）：
- 大幅改动
- 核心逻辑改变
- 涉及生产环境
```

---

## Safety Agent回滚机制

```
自动回滚条件：
- 执行后指标立即恶化
- 验证失败
- 异常错误

回滚流程：
Safety Agent检测 → 自动回滚 → 记录原因 → 通知Hermes → 人知道
```

---

## 人的配置权限

```
通过Hermes配置：
- 风险阈值
- 自动化程度
- 告警条件
- 通知方式
- 哪些需要审批
```

---

## 和CrewAI的关系

```
使用CrewAI的：
- Agent定义
- Task定义
- Crew编排
- 共享上下文

CrewAI和Hermes独立：
- CrewAI是后台自动化引擎
- Hermes是前端对话界面
```

---

## LLM配置

```
Discovery：小型快速模型（高频）
Monitor：小型快速模型（高频）
Proposer：大型推理模型（低频）
Refiner：中型稳定模型（低频）
Safety：小型快速模型（持续）

Hermes：独立大模型（和人类对话）
```

---

## 人的工作量

```
设定规则：一次配置
监控进度：偶尔问Hermes
手动介入：极少数高风险情况
```

---

## 优势

```
1. 真正闭环
   - 系统自己发现机会
   - 系统自己生成建议
   - 系统自己验证效果

2. 高速自动化
   - 99%自动执行
   - 可随时回滚

3. Hermes可选
   - 没有也能跑
   - 只是增强体验

4. 可控
   - 人在监控
   - 高风险必须审批
   - Safety处理紧急情况
```

---

## 动态平衡问题（待解决）

```
问题1：过拟合
- 系统一直改参数，改到完美匹配历史数据
- 但新数据来了就不行了

问题2：震荡
- A→B→A→B来回改
- 永远不稳定

问题3：梯度崩溃
- 一直往一个方向优化
- 到了局部最优就停

问题4：负向优化
- 改完后整体效果变差了
```

---

## 需要的平衡机制

```
1. 约束机制（Guardrails）
   - 什么不能改
   - 什么范围可以动

2. 冷却机制（Cooldown）
   - 改完一次后要等多久才能再改
   - 防止震荡

3. 多样性保护（Diversity）
   - 不能一直优化同一方向
   - 要保留一些"不优化"的候选

4. 回归检测（Regression Detection）
   - 改完后效果下降要能发现
   - 及时回滚

5. 预算控制（Budget Control）
   - 多久优化一次
   - 改动的幅度限制
```

---

## 待讨论

```
- 每个平衡机制怎么实现？
- 哪些是Agent职责？
- 哪些是配置项？
- 怎么避免局部最优陷阱？
```

---

## 版本分支机制（新增）

### 核心概念

```
就像Git的分支：
- 锁定当前配置 = 创建tag/分支
- 继续优化 = 在这个分支上继续
- 重新优化 = 开一个新分支从零开始
```

### 设计

```
Baseline A（锁定） ←─ 人觉得不错，锁定
    ↑
    │ 继续优化
    │
Baseline A'
    ↑
    │ 又改了一次
    │
Baseline A''

---

Baseline B（新分支） ←─ 重新开始
    ↑
    │
Baseline B'
```

### 人的操作

```
1. 锁定（Lock）
   - 把当前配置打tag
   - "这个配置不错，先不动了"

2. 分支（Branch）
   - 基于锁定版本开新分支
   - 在新分支上继续优化

3. 切换（Switch）
   - 切换到某个分支作为主版本

4. 回滚（Rollback）
   - 切回之前的锁定版本
```

### UI操作 vs Hermes对话

```
Hermes（对话）：
"帮我锁定这个配置"
"开一个新分支"
"现在有哪些版本"

UI按钮（直接）：
[锁定当前配置] ← 点击即锁定
[创建新分支]   ← 点击即创建
[切换版本]     ← 选择即切换
[回滚]         ← 选择即回滚
```

### UI布局

```
业务层 → Workflow可视化
              ↓
        当前版本：A'
        [锁定] [分支] [查看历史]
```

### 锁定后的状态

```
锁定后：
- 配置变成只读
- Agent不能自动改这个参数
- 除非开新分支解锁

解锁：
- 人手动解锁
- 或者开新分支后解锁
```

### Agent视角

```
优化时：
- 要知道当前在哪个分支
- 优化的是哪个版本
- 不能跨分支乱改
```

---

## Agent技能配置系统

### 目标

```
让每个Agent可以被独立配置：
- 技能（Skills）
- 工具（Tools）
- MCP servers
- 触发条件
- 约束规则
- LLM模型
```

### 配置方式

```
1. 声明式配置
   - YAML/JSON定义
   - 这个Agent有哪些能力

2. 运行时注入
   - 根据场景动态加载
   - 不同业务用不同配置

3. MCP集成
   - 接入外部MCP工具
   - 扩展Agent能力
```

### Agent需要什么

```
1. 技能（Skills）
   - 会做什么
   - 看数据、分析、生成建议等

2. 工具（Tools）
   - MCP工具
   - API调用
   - 代码执行

3. 知识（Knowledge）
   - 领域知识
   - 历史经验
   - 规则约束
```

### MCP怎么用

```
每个Agent可以配置MCP servers：

Monitor Agent：
- 接入数据库MCP（读数据）
- 接入监控MCP（看指标）

Proposer Agent：
- 接入代码生成MCP（生成改动）
- 接入分析MCP（分析原因）

Refiner Agent：
- 接入执行MCP（执行改动）
- 接入验证MCP（跑测试）
```

### 技能配置示例

```yaml
Monitor Agent:
  skills:
    - data_watch
    - anomaly_detect
  mcp_servers:
    - database_reader
    - metrics_collector
  triggers:
    - schedule: "*/5 * * * *"  # 每5分钟
    - threshold: sharpe < 1.0

Proposer Agent:
  skills:
    - root_cause_analysis
    - proposal_generate
  mcp_servers:
    - code_modifier
    - simulation_runner
  constraints:
    - max_param_change: 20%
    - param_range: {window: [10, 50]}
```

### 配置弹窗（独立UI）

```
业务层 → Agent配置弹窗
              ↓
        点击"配置"按钮
              ↓
        弹窗内配置：
        - 技能列表
        - MCP servers
        - 触发条件
        - 约束规则
        - LLM模型
```

### 弹窗内容

```
Agent技能配置：

技能：
[x] data_watch
[x] anomaly_detect
[ ] trend_analysis

MCP Servers：
[ ] database_reader
[x] metrics_collector
[ ] code_modifier

触发条件：
[ ] 定时：每5分钟
[x] 阈值：sharpe < 1.0

约束：
参数范围：10-50
单次改动：≤20%

LLM模型：
[小型快速模型 ▼]
```

### 和Hermes的关系

```
Hermes：只看、能问、不能改配置
配置弹窗：人直接操作、独立界面
```

---

## 内置 vs 外置Agent系统

### 区分

```
内置Agent系统：
- 5个CrewAI Agent
- 在CheckpointAI内部
- 负责：看数据、分析、生成建议、协调外置系统

外置Agent系统：
- TradingAgents / ContentAgents / CustomerAgents等
- 在CheckpointAI外部
- 负责：实际执行任务
```

### 关系

```
内置Agent（协调者）
    ↓ 生成proposal
    ↓ 审批
    ↓ 改动建议
外置Agent（执行者）
    ↓ 接收改动
    ↓ 执行
    ↓ 报告结果
内置Agent（验证者）
    ↓ 验证效果
    ↓ 更新知识库
```

### 外置Agent接收什么

```
TradingAgents接收：
- 参数改动（moving_average_window: 20 → 18）
- prompt改动
- 策略调整
- 配置更新

但不接收：
- 原始prompt全文
- 业务逻辑
- 核心算法
```

---

## 架构：每个业务线一个内置Agent系统

### 设计原则

```
一个内置系统管所有外置Agent的问题：
- 上下文会污染
- 业务线A的数据影响业务线B
- 监控负担重
- 难以追踪

解决方案：每个业务线一个内置Agent系统
```

### 最终架构

```
业务线A：
  内置Agent系统A
    ↓ 协调
  外置Agent A1, A2, A3

业务线B：
  内置Agent系统B
    ↓ 协调
  外置Agent B1, B2

业务线之间完全隔离
```

### 内置系统的工作

```
Monitor：监控所有外置Agent的数据
Proposer：生成针对某个外置Agent的改动
Refiner：验证改动在对应外置Agent上的效果
```

### Hermes跨业务线

```
Hermes可以：
- 切换业务线视角
- 问A："业务线A最近优化了什么"
- 问B："业务线B的效果怎么样"
- 但不混合上下文
```
