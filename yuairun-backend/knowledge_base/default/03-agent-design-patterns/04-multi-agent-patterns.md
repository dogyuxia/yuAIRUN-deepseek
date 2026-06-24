# Multi-Agent Patterns（多 Agent 模式）

## 概述

多 Agent 模式是指**多个 AI Agent 协作**完成复杂任务的架构。每个 Agent 有专门的职责，通过通信和协作来解决问题。这种模式模拟了人类团队的工作方式。

## 为什么需要多 Agent？

| 单一 Agent 的限制 | 多 Agent 的优势 |
|------------------|----------------|
| 单个角色能力有限 | 多角色专业分工 |
| 没有交叉验证 | 互相审查和验证 |
| 难以处理超长上下文 | 分而治之，降低上下文压力 |
| 单点故障 | 一个失败不影响整体 |

## 常见的多 Agent 架构

### 1. 顺序式 (Sequential)

Agent 按顺序执行，前一个的输出是后一个的输入。

```
用户 → Agent A → Agent B → Agent C → 输出
```

**场景**：写作工作流
```
研究员 Agent → 写作者 Agent → 审核员 Agent → 最终输出
```

### 2. 辩论式 (Debate)

多个 Agent 对同一个问题进行讨论，最终达成共识。

```
         ┌── Agent A ──┐
用户 → ──┼── Agent B ──┼── 讨论 → 共识 → 输出
         └── Agent C ──┘
```

**场景**：代码审查
```
架构师 Agent："这个方案扩展性不够"
安全 Agent："存在 SQL 注入风险"
性能 Agent："这个查询太慢，需要加索引"
→ 综合意见后生成改进方案
```

### 3. 层级式 (Hierarchical)

一个主 Agent 管理多个子 Agent。

```
                主 Agent
             /    |    \
        研究员  写作者  审核员
         Agent  Agent   Agent
```

**场景**：研究项目
```
项目经理 Agent（分配任务）
├── 文献研究 Agent（查资料）
├── 数据分析 Agent（处理数据）
└── 报告撰写 Agent（写报告）
```

### 4. 市场式 (Market-based)

Agent 之间通过竞争或拍卖机制协作。

```
任务发布 → Agent 竞标 → 最优 Agent 执行 → 结果验证
```

**场景**：代码生成
```
"写一个排序函数"
Agent A 报价：10 tokens，复杂度 O(n²)
Agent B 报价：20 tokens，复杂度 O(n log n)
→ 选择 Agent B（质量优先）
```

## LangGraph 实现多 Agent

LangGraph 是 LangChain 专门用于构建**有状态多 Agent 系统**的框架。

### 基本概念

| 概念 | 说明 |
|------|------|
| **Node（节点）** | 一个 Agent 或一个处理步骤 |
| **Edge（边）** | 节点之间的连接，定义数据流向 |
| **State（状态）** | 全局共享的状态对象 |
| **Conditional Edge** | 根据条件动态选择下一个节点 |

### 简单示例

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, Literal

# 定义状态
class AgentState(TypedDict):
    messages: list
    next_agent: str

# 定义节点函数
def researcher(state: AgentState) -> AgentState:
    """研究员 Agent"""
    # 搜索资料
    state["messages"].append("研究完成")
    state["next_agent"] = "writer"
    return state

def writer(state: AgentState) -> AgentState:
    """写作者 Agent"""
    # 根据研究结果撰写
    state["messages"].append("撰写完成")
    state["next_agent"] = "reviewer"
    return state

def reviewer(state: AgentState) -> AgentState:
    """审核员 Agent"""
    # 审核内容
    state["messages"].append("审核通过")
    state["next_agent"] = END
    return state

# 构建图
graph = StateGraph(AgentState)
graph.add_node("researcher", researcher)
graph.add_node("writer", writer)
graph.add_node("reviewer", reviewer)

graph.set_entry_point("researcher")
graph.add_edge("researcher", "writer")
graph.add_edge("writer", "reviewer")
graph.add_edge("reviewer", END)

app = graph.compile()
```

### 带条件的路由

```python
def route_based_on_quality(state: AgentState) -> Literal["writer", END]:
    """根据质量决定是否需要修改"""
    if state.get("needs_revision"):
        return "writer"  # 返回修改
    return END  # 完成

graph.add_conditional_edges("reviewer", route_based_on_quality)
```

## 多 Agent 通信

### 消息格式

```python
class AgentMessage:
    def __init__(self, sender, receiver, content, msg_type):
        self.sender = sender        # 发送者 Agent ID
        self.receiver = receiver    # 接收者 Agent ID
        self.content = content      # 消息内容
        self.msg_type = msg_type     # 消息类型
        self.timestamp = time.time()
```

### 共享记忆

```python
class SharedMemory:
    """多 Agent 共享的工作空间"""
    
    def __init__(self):
        self.context = {}    # 共享上下文
        self.results = {}    # 各 Agent 的结果
        self.log = []        # 操作日志
    
    def update(self, agent_id, data):
        self.results[agent_id] = data
        self.log.append({
            "agent": agent_id,
            "data": data,
            "time": time.time()
        })
```

## 多 Agent vs 单一 Agent

| 场景 | 建议 |
|------|------|
| 简单问答 | 单一 Agent |
| 需要多角色专业知识 | 多 Agent |
| 需要交叉验证 | 多 Agent（辩论式） |
| 长文档处理 | 多 Agent（分而治之） |
| 成本敏感 | 单一 Agent |
| 延迟敏感 | 单一 Agent |

## 最佳实践

1. **角色定义清晰**：每个 Agent 的角色和职责要明确
2. **通信协议标准化**：定义统一的消息格式
3. **避免过度复杂**：2~3 个 Agent 通常足够
4. **人类在环中**：关键决策由人类确认
5. **监控和日志**：记录所有 Agent 的通信和决策
6. **优雅降级**：某个 Agent 失败时不影响整体流程
