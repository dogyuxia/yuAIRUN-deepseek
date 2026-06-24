# LangChain 框架概述

## 什么是 LangChain？

LangChain 是一个开源的 **AI 编排框架**，专门用于构建基于大语言模型（LLM）的应用程序。它提供了标准化的接口和丰富的组件，让开发者能够轻松地将 LLM 与外部数据源、工具和服务集成。

**官方定位**：LangChain is a framework for developing applications powered by language models.

## 核心设计理念

### 1. 组件化（Components）

LangChain 将 AI 应用拆分为可组合的独立组件：

```
┌─────────────────────────────────────────┐
│           LangChain 组件生态             │
├─────────────────────────────────────────┤
│  Model I/O   │   Retrieval   │  Agents  │
│  ─────────── │  ──────────── │  ─────── │
│  • ChatModel │  • Document   │  • Agent │
│  • LLM       │  • Loaders    │  • Tools │
│  • Prompts   │  • Vector     │  • Tool  │
│  • Output    │    Stores     │    kits  │
│    Parsers   │  • Embeddings │          │
├──────────────┼───────────────┼──────────┤
│    Chains    │    Memory     │ Callbacks│
└──────────────┴───────────────┴──────────┘
```

### 2. 可组合性（Composability）

组件通过统一接口可以像搭积木一样组合：

```python
# LangChain Expression Language (LCEL)
chain = prompt | model | output_parser
```

### 3. 可扩展性（Extensibility）

所有组件都设计了抽象基类，可自定义实现。

## 主要组件详解

### Model I/O（模型输入输出）

| 组件 | 说明 |
|------|------|
| **ChatModel** | 聊天模型接口（OpenAI、DeepSeek、Claude 等） |
| **PromptTemplate** | Prompt 模板管理，支持变量填充 |
| **OutputParser** | 输出解析器，将 LLM 输出转为结构化数据 |

### Retrieval（检索）

| 组件 | 说明 |
|------|------|
| **Document Loaders** | 文档加载器（PDF、HTML、数据库等） |
| **Text Splitters** | 文本分割器（按字符、按语义分块） |
| **Vector Stores** | 向量数据库接口（ChromaDB、FAISS、Milvus 等） |
| **Embeddings** | 文本嵌入模型接口 |
| **Retrievers** | 检索器（向量检索、上下文压缩、多查询） |

### Agents（代理）

| 组件 | 说明 |
|------|------|
| **Agent** | Agent 执行器，协调 LLM 和工具 |
| **Tools** | 工具接口（搜索、计算、API 调用等） |
| **Toolkits** | 工具包（一组相关工具的集合） |
| **AgentExecutor** | Agent 执行引擎，管理思考-行动循环 |

### Chains（链）

| 类型 | 说明 |
|------|------|
| **LLMChain** | 最基本的 Prompt → LLM → 输出链 |
| **SequentialChain** | 按顺序执行多个链 |
| **RouterChain** | 根据输入路由到不同子链 |
| **LCEL** | LangChain Expression Language，声明式链构建 |

### Memory（记忆）

| 类型 | 说明 |
|------|------|
| **ConversationBufferMemory** | 存储完整对话历史 |
| **ConversationSummaryMemory** | 压缩摘要存储 |
| **VectorStoreMemory** | 基于向量检索的记忆 |
| **PostgresChatMessageHistory** | 持久化对话历史到数据库 |

### Callbacks（回调）

用于监控、日志、流式输出等：
- 事件类型：on_llm_start, on_chain_end, on_tool_start 等
- 用途：日志记录、性能监控、流式输出

## 核心优势

| 优势 | 说明 |
|------|------|
| **标准化接口** | 统一不同 LLM 提供商的 API 差异 |
| **丰富的集成** | 500+ 集成（模型、向量库、工具、数据源） |
| **LCEL 语法** | 简洁的声明式链构建语法 |
| **生产就绪** | 内置重试、超时、回调、流式等 |
| **活跃社区** | 最大的 LLM 应用开发社区 |

## LangChain 生态系统

```
LangChain
├── LangChain（核心框架）
├── LangSmith（调试、测试、监控平台）
├── LangGraph（有状态 Agent / 多 Agent 编排）
├── LangServe（API 部署）
└── LangChain Template（项目模板）
```

## 在本项目中的使用

本系统（yuAIRUN）使用 LangChain 实现：
1. **出题链**：Prompt 模板 → DeepSeek → 结构化输出（with_structured_output）
2. **搜索增强 Agent**：TavilySearch + TavilyExtract 工具驱动出题
3. **RAG 出题链**：ChromaDB 向量检索 → 上下文注入 → 出题
