# ReAct Pattern（推理+行动模式）

## 概述

**ReAct** 是 "Reasoning + Acting" 的缩写，由 Shunyu Yao 等人在 2022 年提出。它是目前最广泛使用的 AI Agent 工作模式，核心思想是**将推理和行动交织进行**。

论文：[ReAct: Synergizing Reasoning and Acting in Language Models](https://arxiv.org/abs/2210.03629)

## 核心流程

```
循环直到任务完成：
    1. Thought（思考）：分析当前状态，决定下一步
    2. Action（行动）：执行一个具体的工具调用
    3. Observation（观察）：获取工具返回的结果
    4. 回到步骤 1
```

### 可视化流程

```
用户："2024年诺贝尔物理学奖得主是谁？他有什么主要贡献？"

Thought: 用户想知道2024年诺贝尔物理学奖得主及其贡献。
         我需要先搜索这个信息。
Action: web_search({"query": "2024 Nobel Prize in Physics"})
Observation: 2024年诺贝尔物理学奖授予 John Hopfield 和 Geoffrey Hinton...

Thought: 现在我知道得主是 John Hopfield 和 Geoffrey Hinton。
         他们以人工神经网络和深度学习的基础发现和发明获奖。
         我需要整理回答。
Action: 无（已获得足够信息）
Output: 2024年诺贝尔物理学奖授予了...
```

## ReAct 的 Prompt 模板

```text
你是一个能思考并采取行动的AI助手。

你按以下格式回复：

问题: 用户提出的问题
思考: 分析当前情况，决定下一步行动
行动: 调用的工具名称
行动输入: 工具的输入参数
观察: 工具返回的结果
...（思考-行动-观察可以重复多次）
思考: 我现在可以回答用户的问题了
最终回答: 对用户的完整回答

你有以下工具可用：
{tools}

开始！
问题: {input}
```

## 实现示例

### 使用 LangChain 创建 ReAct Agent

```python
from langchain.agents import create_react_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_tavily import TavilySearch

# 创建工具
tools = [TavilySearch(max_results=3)]

# 创建 LLM
llm = ChatOpenAI(model="deepseek-chat", temperature=0)

# 创建 ReAct Agent
agent = create_react_agent(
    model=llm,
    tools=tools,
    system_prompt="你是一个研究助手，搜索并回答问题。",
)

# Agent 执行器（管理思考-行动循环）
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,        # 打印思考过程
    max_iterations=5,    # 最大迭代次数
    handle_parsing_errors=True,  # 处理解析错误
)

# 运行 Agent
result = agent_executor.invoke({
    "input": "什么是 ReAct Pattern？"
})
```

## ReAct 的关键特性

| 特性 | 说明 |
|------|------|
| **推理可见** | Agent 的思考过程可追溯，可调试 |
| **动态决策** | 每次行动后重新评估下一步 |
| **错误恢复** | 工具调用失败时可以重新尝试 |
| **早停机制** | 信息足够时可提前结束 |

## ReAct 的局限性

| 问题 | 说明 | 改进方案 |
|------|------|---------|
| **Token 消耗大** | 每次循环都要消耗大量 token | 限制 max_iterations |
| **循环陷阱** | 可能陷入无限循环 | 设置最大迭代次数 |
| **错误累积** | 早期错误会影响后续决策 | 增加验证步骤 |
| **工具延迟** | 每次工具调用都有延迟 | 并行调用独立工具 |

## ReAct vs 其他模式

| 对比 | ReAct | Plan & Execute | Tool-Use |
|:----:|:-----:|:--------------:|:--------:|
| 规划方式 | 边做边想 | 先规划再执行 | 按需调用 |
| 灵活性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| Token 效率 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 复杂任务 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 实现难度 | ⭐⭐ | ⭐⭐⭐ | ⭐ |

## 最佳实践

1. **限制迭代次数**：`max_iterations=5~10` 防止无限循环
2. **设置早停条件**：当置信度足够高时提前结束
3. **错误处理**：工具失败时记录日志并重试
4. **上下文管理**：定期压缩过长的思考历史
5. **并行行动**：独立的任务可以并行调用工具
