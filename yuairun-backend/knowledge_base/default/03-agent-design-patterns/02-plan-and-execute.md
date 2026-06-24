# Plan-and-Execute Pattern（规划与执行模式）

## 概述

Plan-and-Execute（计划与执行）模式将任务分解为两个阶段：
1. **规划阶段**：LLM 先制定一个完整的执行计划
2. **执行阶段**：按计划逐步执行，每步可以调用工具

这种模式适合**复杂、多步骤**的任务，如撰写长文、数据分析、项目策划等。

## 核心流程

```
第一阶段：规划
用户输入 → LLM 制定计划 → 输出结构化的步骤列表

第二阶段：执行
步骤1 → 执行 → 检查结果 → 步骤2 → ... → 完成
```

### 可视化流程

```
用户："帮我写一篇关于 AI Agent 的技术文章"

第一阶段 - 规划：
LLM 输出计划：
  1. 搜索 AI Agent 最新发展
  2. 阅读 3 篇高质量参考文章
  3. 制定文章大纲
  4. 撰写各章节
  5. 润色和校对

第二阶段 - 执行：
  Step 1: [搜索] → 获取 5 篇相关文章
  Step 2: [阅读] → 提取关键信息和观点
  Step 3: [生成大纲] → 确认用户满意
  Step 4: [撰写] → 逐章输出
  Step 5: [润色] → 最终稿
```

## 规划示例

```python
from langchain.chains.plan_and_execute import (
    PlanAndExecute,
    load_agent_executor,
    load_chat_planner,
)
from langchain_openai import ChatOpenAI
from langchain_tavily import TavilySearch

# 工具
tools = [TavilySearch(max_results=3)]

# 规划器（负责拆解任务）
planner = load_chat_planner(ChatOpenAI(model="deepseek-chat"))

# 执行器（负责逐步执行）
executor = load_agent_executor(
    ChatOpenAI(model="deepseek-chat"),
    tools=tools,
    verbose=True,
)

# 组合
agent = PlanAndExecute(
    planner=planner,
    executor=executor,
    verbose=True,
)
```

## 规划输出格式

LLM 制定的计划通常采用结构化格式：

```json
{
  "plan": {
    "goal": "写一篇关于 AI Agent 的技术文章",
    "steps": [
      {
        "step": 1,
        "description": "搜索 AI Agent 最新发展",
        "tools_needed": ["web_search"]
      },
      {
        "step": 2,
        "description": "阅读 3 篇高质量参考文章",
        "tools_needed": ["web_extract"]
      },
      {
        "step": 3,
        "description": "制定文章大纲",
        "tools_needed": []
      },
      {
        "step": 4,
        "description": "逐章撰写内容",
        "tools_needed": []
      }
    ]
  }
}
```

## 动态重规划

Plan-and-Execute 的一个重要特性是**执行过程中可以动态调整计划**：

```
执行步骤 2（阅读文章）时发现：
  - 这些文章提到了一个重要的新概念
  - 之前计划没有覆盖到这个概念
  - → 插入新步骤 2.5：搜索该概念的更多资料
```

```python
class DynamicPlanner:
    """支持动态调整的规划器"""
    
    async def execute_with_replan(self, plan, executor):
        results = []
        for i, step in enumerate(plan["steps"]):
            result = await executor.astep(step)
            results.append(result)
            
            # 检查是否需要调整计划
            if self.should_replan(result):
                new_plan = await self.replan(plan, results)
                return await self.execute_with_replan(new_plan, executor)
        
        return results
```

## 优劣分析

### 优点

| 优点 | 说明 |
|------|------|
| **结构化** | 清晰的执行路径，易于理解和审查 |
| **可预测** | 先看到完整计划，再开始执行 |
| **可干预** | 用户可以在规划阶段修改计划 |
| **适合复杂任务** | 比 ReAct 更适合需要全局视角的任务 |

### 缺点

| 缺点 | 说明 |
|------|------|
| **计划可能不准确** | LLM 的初始计划可能遗漏关键步骤 |
| **灵活性较低** | 不如 ReAct 灵活应对变化 |
| **额外开销** | 规划阶段也消耗 token |
| **任务边界模糊时不佳** | 需要任务有清晰的结构 |

## 何时使用 Plan-and-Execute？

| 适合的场景 | 不适合的场景 |
|-----------|-------------|
| 撰写长文章/报告 | 简单的问答任务 |
| 数据分析项目 | 实时交互式对话 |
| 多步骤研究任务 | 需要快速响应的场景 |
| 项目策划方案 | 不可预测的用户需求 |
| 学习路径规划 | 单一工具调用即可完成的任务 |

## 最佳实践

1. **规划要具体**：步骤描述要清晰，包含需要使用的工具
2. **设置步骤上限**：防止计划过于庞大（建议 5~8 步）
3. **允许重新规划**：执行中发现新信息时可以调整计划
4. **人类审核环节**：关键决策点允许用户确认
5. **结果累积**：每步结果传递到下一步作为上下文
