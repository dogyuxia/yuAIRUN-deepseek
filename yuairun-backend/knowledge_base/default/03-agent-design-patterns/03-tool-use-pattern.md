# Tool-Use Pattern（工具使用模式）

## 概述

Tool-Use 模式（也称为 Function Calling）是 AI Agent 最基础也最重要的能力。它让 LLM 能够**调用外部工具**来获取信息、执行操作，而不仅仅是生成文本。

## Function Calling 的工作原理

```
用户："帮我查一下北京的天气"

LLM 内部处理：
1. 理解意图：用户想知道北京的天气
2. 匹配工具：有一个 get_weather 工具可以满足
3. 生成函数调用：get_weather(city="北京")
4. 返回结构化调用请求

系统层面：
1. 收到 LLM 返回的函数调用请求
2. 执行 get_weather("北京")
3. 将结果返回给 LLM
4. LLM 基于结果生成自然语言回复
```

## 工具定义方式

### OpenAI 风格的 Function Calling

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "获取指定城市的天气信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称"
                    },
                    "date": {
                        "type": "string",
                        "description": "日期，格式 YYYY-MM-DD，可选"
                    }
                },
                "required": ["city"]
            }
        }
    }
]

# LLM 返回的函数调用
response = {
    "tool_calls": [
        {
            "id": "call_xxx",
            "type": "function",
            "function": {
                "name": "get_weather",
                "arguments": '{"city": "北京", "date": "2024-12-25"}'
            }
        }
    ]
}
```

### LangChain Tool 定义

```python
from langchain_core.tools import tool

@tool
def get_weather(city: str, date: str = None) -> str:
    """获取指定城市的天气信息
    
    Args:
        city: 城市名称
        date: 日期，格式 YYYY-MM-DD，不传则查今天
    """
    # 实际调用天气 API
    return f"{city} {date or '今天'} 的天气：晴，18-25°C"
```

## 工具调用的完整流程

```
用户输入
    │
    ▼
┌──────────────────────┐
│ LLM 分析输入          │
│ 判断是否需要工具调用   │
└──────────┬───────────┘
           │
    ┌──────┴──────┐
    ▼              ▼
不需要工具      需要工具
    │              │
    ▼              ▼
直接回复        LLM 生成工具调用
    │           (函数名+参数)
    │              │
    │              ▼
    │        执行工具函数
    │              │
    │         ┌────┴────┐
    │         ▼         ▼
    │      成功        失败
    │         │         │
    │         ▼         ▼
    │    获取结果    获取错误
    │         │         │
    │         ▼         ▼
    │    LLM 处理结果  LLM 处理错误
    │         │         │
    └────┬────┘         │
         ▼              ▼
      最终回复      错误回复或重试
```

## 多工具协同

### 按条件选择工具

```python
@tool
def search_database(query: str) -> str:
    """查询内部数据库"""
    pass

@tool
def search_web(query: str) -> str:
    """搜索互联网"""
    pass

@tool
def calculate(expression: str) -> str:
    """执行数学计算"""
    pass

# LLM 根据问题特点自动选择合适的工具
```

### 工具链式调用

```python
# 场景：计算 2024 年北京市 GDP 增长率
# Step 1: search_web("2023年北京GDP")
# Step 2: search_web("2024年北京GDP")
# Step 3: calculate("(2024GDP - 2023GDP) / 2023GDP * 100")
```

## 工具调用的安全考虑

| 安全措施 | 说明 |
|---------|------|
| **工具白名单** | 只允许调用预定义的合法工具 |
| **参数校验** | 对工具输入参数做类型和范围检查 |
| **速率限制** | 限制工具调用频率，防止滥用 |
| **操作确认** | 危险操作（删除、修改）需要用户确认 |
| **审计日志** | 记录所有工具调用，便于追溯 |

## Tool-Use vs ReAct

| 对比 | Tool-Use | ReAct |
|:----:|:--------:|:-----:|
| 是否思考 | 直接调用工具 | 先思考再行动 |
| 多步推理 | 有限 | 原生支持 |
| 实现复杂度 | 低 | 中 |
| 适用场景 | 简单的工具调用 | 需要推理的复杂任务 |

## 最佳实践

1. **工具描述要精准**：LLM 靠 description 判断何时使用工具
2. **参数类型要明确**：使用类型注解帮助 LLM 生成正确参数
3. **错误处理要完善**：工具报错时返回友好信息，不要崩溃
4. **幂等性设计**：重复调用相同参数应得到相同结果
5. **超时控制**：每个工具调用设置超时，防止卡死
