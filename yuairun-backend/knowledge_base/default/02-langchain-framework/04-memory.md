# LangChain Memory（记忆系统）

## 什么是 Memory？

Memory（记忆）是 AI Agent 的重要组成部分，它让 Agent 能够**记住之前的交互内容**，实现连贯的多轮对话和跨 Session 的知识保留。

## 记忆的类型

```
短期记忆（Session内）        长期记忆（跨Session）
┌──────────────────┐        ┌──────────────────┐
│  对话上下文        │        │  向量数据库       │
│  (Token窗口内)    │        │  (RAG)           │
├──────────────────┤        ├──────────────────┤
│  BufferMemory    │        │  VectorStore     │
│  SummaryMemory   │        │  Memory          │
│  WindowMemory    │        └──────────────────┘
└──────────────────┘
```

## 短期记忆实现

### 1. ConversationBufferMemory（完整对话缓冲）

存储最近的对话历史，不压缩。

```python
from langchain.memory import ConversationBufferMemory

memory = ConversationBufferMemory()
memory.chat_memory.add_user_message("你好")
memory.chat_memory.add_ai_message("你好！有什么可以帮助你的？")

# 获取记忆
memory.load_memory_variables({})
# {'history': 'Human: 你好\nAI: 你好！有什么可以帮助你的？'}
```

### 2. ConversationBufferWindowMemory（窗口记忆）

只保留最近的 k 轮对话。

```python
from langchain.memory import ConversationBufferWindowMemory

memory = ConversationBufferWindowMemory(k=3)
# 只保留最近 3 轮对话，更早的自动丢弃
```

### 3. ConversationSummaryMemory（摘要记忆）

将完整的对话历史压缩为摘要，节省 token。

```python
from langchain.memory import ConversationSummaryMemory
from langchain_openai import ChatOpenAI

memory = ConversationSummaryMemory(
    llm=ChatOpenAI(),
    max_token_limit=200,  # 摘要的最大 token 数
)
```

### 4. 组合使用

```python
from langchain.memory import (
    ConversationSummaryBufferMemory,
)

memory = ConversationSummaryBufferMemory(
    llm=ChatOpenAI(),
    max_token_limit=1000,
    # 在 token 数超过限制时自动压缩为摘要
)
```

## 长期记忆实现

### 1. VectorStoreRetrieverMemory（向量检索记忆）

使用向量数据库存储和检索历史。

```python
from langchain.memory import VectorStoreRetrieverMemory
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")
vector_store = Chroma(embedding_function=embeddings)

memory = VectorStoreRetrieverMemory(
    retriever=vector_store.as_retriever(search_kwargs={"k": 3}),
    memory_key="history",
)
```

### 2. 持久化对话历史

```python
from langchain.memory import PostgresChatMessageHistory

# 使用 PostgreSQL 持久化对话历史
history = PostgresChatMessageHistory(
    connection_string="postgresql://user:pass@localhost/db",
    session_id="user_session_001",
)
history.add_user_message("你好")
history.add_ai_message("你好！")
```

## Memory 与 Chain 的集成

### 在 Chain 中使用 Memory

```python
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "你是一个AI助手"),
    ("human", "{input}"),
])

chain = LLMChain(
    llm=ChatOpenAI(),
    prompt=prompt,
    memory=ConversationBufferMemory(),
)

# 第一次对话
chain.invoke({"input": "你好"})
# 第二次对话（Chain 自动注入历史）
chain.invoke({"input": "我刚才说了什么？"})
```

### 在 LCEL 中使用 Memory

```python
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory

chain = prompt | model | output_parser

chain_with_history = RunnableWithMessageHistory(
    chain,
    get_session_history=lambda session_id: InMemoryChatMessageHistory(),
    input_messages_key="input",
    history_messages_key="history",
)

result = chain_with_history.invoke(
    {"input": "你好"},
    config={"configurable": {"session_id": "user_001"}},
)
```

## Agent 的记忆

Agent 的记忆比 Chain 更复杂，因为 Agent 需要记住：
1. **对话历史**：用户和 AI 的对话
2. **思考轨迹**：Agent 的每一步推理
3. **工具调用结果**：每次工具调用的输入和输出

### Agent 的内存管理

```python
from langchain.agents import AgentExecutor, create_react_agent
from langchain.memory import ConversationSummaryBufferMemory

memory = ConversationSummaryBufferMemory(
    llm=ChatOpenAI(),
    max_token_limit=2000,
    memory_key="chat_history",
)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    memory=memory,
    verbose=True,
    max_iterations=10,  # 防止无限循环
)
```

## 记忆系统的最佳实践

| 实践 | 说明 |
|------|------|
| **限制上下文长度** | 设置 max_token_limit，避免超长上下文 |
| **合理使用摘要** | 长对话使用 SummaryMemory 节省 token |
| **会话隔离** | 使用 session_id 区分不同用户/会话 |
| **定期清理** | 长期运行的服务定期清理过期会话 |
| **向量检索阈值** | 设置相似度阈值，避免检索到无关内容 |

## 本项目中的记忆应用

在 yuAIRUN 系统中，记忆系统体现在：
1. **短期记忆**：Zustand 状态管理保持当前答题会话状态
2. **长期记忆**：MySQL 数据库持久化用户数据、答题历史
3. **RAG 记忆**：ChromaDB 向量存储用于知识库检索
