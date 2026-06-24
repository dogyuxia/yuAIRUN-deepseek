# LangChain Chains（链）

## 什么是 Chain？

Chain（链）是 LangChain 中**将多个处理步骤串联起来**的核心概念。一个 Chain 可以包含 Prompt → LLM → OutputParser 的简单组合，也可以包含多个子 Chain 的复杂编排。

## LCEL：LangChain Expression Language

LCEL 是 LangChain 推荐的声明式链构建方式，使用 `|` 管道操作符将组件串联：

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 一个简单的链：Prompt → LLM → 输出解析
chain = ChatPromptTemplate.from_template("讲一个关于{topic}的笑话") | ChatOpenAI() | StrOutputParser()

# 调用链
result = chain.invoke({"topic": "程序员"})
```

### LCEL 的核心特性

| 特性 | 说明 |
|------|------|
| **管道语法** | `component1 | component2 | component3` |
| **流式支持** | 任何 LCEL 链都自动支持 `.stream()` 方法 |
| **异步支持** | 自动支持 `.ainvoke()` 和 `.astream()` |
| **批处理支持** | 自动支持 `.batch()` 同时处理多个输入 |
| **并行执行** | 使用 `RunnableParallel` 实现并行 |

### 常用 Runnable 组件

| Runnable | 用途 |
|----------|------|
| `RunnablePassthrough` | 透传输入，常用于保存中间结果 |
| `RunnableParallel` | 并行执行多个子任务 |
| `RunnableLambda` | 将任意 Python 函数转为 Runnable |
| `RunnableBranch` | 条件路由 |
| `RunnableMap` | 对字典输入做变换 |

## 常见 Chain 模式

### 1. 基础链（Prompt → LLM → Output）

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个AI助手"),
    ("human", "{input}"),
])
chain = prompt | ChatOpenAI() | StrOutputParser()
```

### 2. 结构化输出链

使用 `with_structured_output` 直接绑定 Pydantic 模型，LLM 输出自动解析为结构化数据：

```python
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

class QuizQuestion(BaseModel):
    question: str = Field(description="题目")
    answer: str = Field(description="答案")
    options: list[str] = Field(description="选项列表")

llm = ChatOpenAI(model="deepseek-chat")
structured_llm = llm.with_structured_output(QuizQuestion)

result: QuizQuestion = structured_llm.invoke("出一道关于TCP三次握手的题")
```

**优点**：
- 100% 合规 JSON 输出
- 无需手动正则解析
- 类型安全，IDE 智能提示

### 3. 并行链

```python
from langchain_core.runnables import RunnableParallel

# 并行执行多个分析
chain = RunnableParallel(
    summary=summary_chain,
    keywords=keyword_chain,
    sentiment=sentiment_chain,
)

result = chain.invoke({"text": "这是一段需要分析的文字"})
# result = {"summary": "...", "keywords": [...], "sentiment": "..."}
```

### 4. 带条件路由的链

```python
from langchain_core.runnables import RunnableBranch

# 根据输入类别路由到不同的处理器
chain = RunnableBranch(
    (lambda x: x["category"] == "tech", tech_chain),
    (lambda x: x["category"] == "science", science_chain),
    default_chain,  # 兜底
)
```

### 5. Agent 链

Agent 链是一种特殊的链，它包含"思考-行动-观察"循环：

```python
from langchain.agents import create_agent
from langchain_tavily import TavilySearch

tools = [TavilySearch(max_results=3)]
agent = create_agent(model=llm, tools=tools, system_prompt="...")
result = await agent.ainvoke({"messages": [{"role": "user", "content": "..."}]})
```

## Chain 中的关键方法

| 方法 | 同步 | 异步 | 说明 |
|------|:----:|:----:|------|
| `invoke` | ✅ | ❌ | 同步调用 |
| `ainvoke` | ❌ | ✅ | 异步调用 |
| `stream` | ✅ | ❌ | 同步流式输出 |
| `astream` | ❌ | ✅ | 异步流式输出 |
| `batch` | ✅ | ❌ | 批量处理 |
| `abatch` | ❌ | ✅ | 异步批量处理 |

## 调试技巧

### 查看 Chain 内部的中间步骤

```python
# 使用 RunnablePassthrough 调试
from langchain_core.runnables import RunnablePassthrough

chain = (
    RunnablePassthrough.assign(prompted=lambda x: prompt.invoke(x))
    | model
    | output_parser
)
```

### 设置回调查看详细日志

```python
from langchain_core.callbacks import FileCallbackHandler

chain.invoke(input, config={"callbacks": [FileCallbackHandler("log.txt")]})
```
