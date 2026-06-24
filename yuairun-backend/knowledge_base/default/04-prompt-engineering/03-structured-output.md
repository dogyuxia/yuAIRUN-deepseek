# 结构化输出（Structured Output）

## 什么是结构化输出？

结构化输出是指让 LLM 返回**符合预定义 Schema 的数据**（如 JSON），而不是自由文本。这是构建可靠 AI 应用的关键技术。

## 为什么需要结构化输出？

| 场景 | 自由文本的痛点 | 结构化输出的优势 |
|------|---------------|-----------------|
| API 响应 | 需要正则/LLM 二次解析 | 直接反序列化为对象 |
| 数据入库 | 格式不一致 | Schema 约束保证一致性 |
| 前端渲染 | 需要额外处理 | 直接绑定到 UI 组件 |
| 链式调用 | 下游无法解析 | 类型安全传递 |

## 实现方式对比

### 方法 1：在 Prompt 中指定 JSON 格式（传统方式）

```python
SYSTEM_PROMPT = """
请按以下 JSON 格式输出：
{
  "questions": [
    {
      "question": "...",
      "options": [{"label": "A", "content": "..."}],
      "answer": "..."
    }
  ]
}
"""
```

**问题**：LLM 偶尔会格式错误，需要正则解析和错误处理。

### 方法 2：with_structured_output（推荐方式）

```python
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI

class QuizQuestion(BaseModel):
    """单道题目"""
    id: str = Field(description="题目唯一ID")
    type: str = Field(description="题目类型")
    question: str = Field(description="题目内容")
    options: list[dict] = Field(description="选项列表")
    answer: str | list[str] = Field(description="正确答案")
    explanation: str = Field(description="详细解析")
    difficulty: str = Field(description="难度")
    knowledgePoint: str = Field(description="知识点标签")

class QuizResponse(BaseModel):
    """题目集合"""
    questions: list[QuizQuestion] = Field(description="题目列表")
    metadata: dict = Field(description="元数据")

# 绑定 Pydantic 模型
llm = ChatOpenAI(model="deepseek-chat")
structured_llm = llm.with_structured_output(QuizResponse)

# LLM 100% 返回合规的结构化数据
result: QuizResponse = await structured_llm.ainvoke(prompt)
```

## Pydantic 模型最佳实践

### 1. 清晰的字段描述

```python
class QuizOption(BaseModel):
    label: str = Field(description="选项标签，如 A/B/C/D")
    content: str = Field(description="选项内容文本")
```

### 2. 合理的默认值

```python
class QuizMetadata(BaseModel):
    subject: str = Field(description="学科")
    topic: str = Field(description="知识点")
    generatedAt: str = Field(default="", description="生成时间")
    searchEnhanced: bool = Field(default=False, description="是否使用了搜索增强")
    searchSources: list[str] = Field(default=[], description="搜索来源")
```

### 3. 使用 Literal 约束值范围

```python
from typing import Literal

class QuizQuestion(BaseModel):
    type: Literal["single", "multiple", "judge"] = Field(
        description="题目类型"
    )
    difficulty: Literal["easy", "medium", "hard"] = Field(
        description="难度"
    )
    knowledgeSource: Literal["web_search", "model_knowledge", "knowledge_base"] = Field(
        default="model_knowledge",
        description="知识来源"
    )
```

### 4. 嵌套模型

```python
class QuizQuestion(BaseModel):
    id: str
    type: str
    question: str
    options: list[QuizOption]  # 嵌套子模型
    answer: str | list[str]
    explanation: str
    difficulty: str
    knowledgePoint: str
    knowledgeSource: str

class QuizResponse(BaseModel):
    questions: list[QuizQuestion]  # 嵌套列表
    metadata: QuizMetadata
```

## 错误处理

即使使用 with_structured_output，也应该做错误处理：

```python
from langchain_core.exceptions import OutputParserException

try:
    result = await structured_llm.ainvoke(prompt)
    return QuizResponse(**result.model_dump())
except OutputParserException as e:
    logger.error(f"结构化输出解析失败: {e}")
    # 降级：尝试手动解析
    raw = await llm.ainvoke(prompt)
    return parse_and_fix(raw.content)
except Exception as e:
    logger.error(f"LLM 调用失败: {e}")
    # 降级：返回固定 mock 数据
    return get_fallback_response()
```

## JSON Mode vs Function Calling

| 对比 | JSON Mode | Function Calling |
|:----:|:---------:|:----------------:|
| **原理** | 在 Prompt 中指定 JSON Schema | LLM 原生函数调用能力 |
| **稳定性** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **支持的模型** | 大部分模型 | OpenAI、DeepSeek 等 |
| **复杂 Schema** | 简单 Schema 表现好 | 复杂嵌套 Schema 稳定 |
| **推荐场景** | 输出格式简单 | 输出格式复杂 |

> 在 LangChain 中，`with_structured_output` 会自动选择最佳方式（优先用 Function Calling，不支持则用 JSON Mode）。

## 在本项目中的应用

yuAIRUN 大量使用结构化输出：

```python
# 出题链
structured_llm = llm.with_structured_output(QuizResponse)
chain = prompt | structured_llm
result = await chain.ainvoke({"topic": topic})

# 结果直接是类型安全的 Pydantic 对象
for question in result.questions:
    print(f"{question.id}: {question.question}")
    print(f"答案: {question.answer}")
    print(f"来源: {question.knowledgeSource}")
```

## 最佳实践总结

1. **始终使用 with_structured_output**：比手写 JSON 解析更可靠
2. **字段描述要详细**：帮助 LLM 理解每个字段的含义
3. **使用 Literal 约束**：限定枚举值范围
4. **设置默认值**：防止字段缺失导致报错
5. **保留降级逻辑**：LLM 偶尔会失败，做好兜底
6. **渐进式复杂度**：先从简单的 Schema 开始，逐渐增加字段
