# LangChain Tools & Toolkits

## 什么是 Tool？

Tool（工具）是 AI Agent 与外部世界交互的**接口**。每个 Tool 封装了一个具体的能力，Agent 可以通过 LLM 的 function calling 能力调用这些工具。

## Tool 的基本结构

一个 Tool 包含以下要素：

| 要素 | 说明 | 示例 |
|------|------|------|
| **name** | 工具名称（唯一标识） | `"web_search"` |
| **description** | 工具描述（LLM 据此决定何时调用） | `"搜索互联网获取最新信息"` |
| **args_schema** | 参数 Schema（Pydantic 模型） | `{"query": str, "max_results": int}` |
| **func** | 实际执行函数 | 搜索 API 调用 |

### 最简单的 Tool 定义

```python
from langchain_core.tools import tool

@tool
def get_weather(city: str) -> str:
    """获取指定城市的天气情况"""
    # 调用天气 API
    return f"{city} 的天气是晴天，25°C"

# Tool 自动从函数签名和文档字符串提取 name、description 和参数
```

### 更复杂的 Tool

```python
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from typing import Optional

class SearchInput(BaseModel):
    query: str = Field(description="搜索关键词")
    max_results: int = Field(default=5, description="最大返回结果数")
    time_range: Optional[str] = Field(default=None, description="时间范围")

@tool(args_schema=SearchInput)
def web_search(query: str, max_results: int = 5, time_range: Optional[str] = None) -> list[dict]:
    """搜索互联网获取最新信息"""
    # 实现搜索逻辑
    pass
```

## 常用内置工具

### 1. TavilySearch（网络搜索）

```python
from langchain_tavily import TavilySearch

tavily_search = TavilySearch(
    max_results=5,
    topic="general",  # "general" 或 "news"
)

# 在 Agent 中使用
agent = create_agent(model=llm, tools=[tavily_search])
```

### 2. TavilyExtract（页面内容提取）

```python
from langchain_tavily import TavilyExtract

tavily_extract = TavilyExtract(
    extract_depth="advanced",  # "basic" 或 "advanced"
)

# 提取 URL 的完整内容
# 在 Agent 中自动调用
```

### 3. 算术计算

```python
from langchain_core.tools import tool
import math

@tool
def calculator(expression: str) -> str:
    """执行数学计算，输入应为数学表达式"""
    try:
        return str(eval(expression))
    except:
        return "计算错误"
```

### 4. 代码执行

```python
from langchain_experimental.tools import PythonREPLTool

python_tool = PythonREPLTool()
# Agent 可以用它执行 Python 代码来分析数据
```

### 5. 文件操作

| 工具 | 用途 |
|------|------|
| `ReadFileTool` | 读取文件内容 |
| `WriteFileTool` | 写入文件 |
| `ListDirectoryTool` | 列出目录内容 |
| `CopyFileTool` | 复制文件 |

## Toolkits（工具包）

Toolkit 是一组**相关工具的集合**，用于完成某个领域的完整任务。

### 常用 Toolkit

| Toolkit | 包含的工具 | 用途 |
|---------|-----------|------|
| **SQLDatabaseToolkit** | 查询表、执行 SQL、检查语法 | 数据库交互 |
| **GitHubToolkit** | 创建 Issue、PR、读取代码 | GitHub 操作 |
| **FileManagementToolkit** | 读/写/列目录/复制/移动 | 文件管理 |
| **RequestsToolkit** | GET/POST/PUT/DELETE | HTTP 请求 |
| **VectorStoreToolkit** | 向量检索 | RAG 应用 |

### 自定义 Toolkit

```python
from langchain.agents import Tool, tool
from langchain.agents.agent_toolkits.base import BaseToolkit

class CustomToolkit(BaseToolkit):
    """自定义工具包"""
    
    def get_tools(self):
        return [
            Tool(
                name="tool1",
                func=self.tool1_func,
                description="工具1的描述"
            ),
            Tool(
                name="tool2",
                func=self.tool2_func,
                description="工具2的描述"
            ),
        ]
```

## 工具设计原则

### 1. 描述要精确

工具的 `description` 是 LLM 判断何时调用的唯一依据：

```
❌ 不好的描述："一个搜索工具"
✅ 好的描述："搜索互联网获取实时信息，当用户问及最新事件、人物、技术时使用"
```

### 2. 参数要明确

```python
# ❌ 模糊的参数
@tool
def search(query):
    """搜索"""

# ✅ 清晰的参数
@tool(args_schema=SearchInput)
def search(query: str, max_results: int = 5):
    """搜索互联网获取最新信息，支持指定返回结果数量"""
```

### 3. 错误要优雅

```python
@tool
def call_api(url: str) -> dict:
    """调用外部 API"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.Timeout:
        return {"error": "API 请求超时"}
    except requests.RequestException as e:
        return {"error": f"API 请求失败: {str(e)}"}
```

## Tool 在 Agent 中的工作流程

```
用户输入
    │
    ▼
LLM 分析：需要搜索互联网获取最新信息
    │
    ▼
LLM 决定调用 web_search 工具
    │ 参数：{"query": "2024 AI Agent 最新进展", "max_results": 5}
    ▼
工具执行，返回结果
    │
    ▼
LLM 观察结果，决定：还需要获取某篇文章的详细内容
    │
    ▼
LLM 调用 tavily_extract 工具
    │ 参数：{"urls": ["https://..."], "extract_depth": "advanced"}
    ▼
工具执行，返回详细内容
    │
    ▼
LLM 综合所有信息，生成最终回答
```
