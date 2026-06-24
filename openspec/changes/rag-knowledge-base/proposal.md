## Why

当前系统已实现"搜索增强出题"（Tavily 驱动），但依赖公开互联网，无法覆盖企业内部知识、私密文档、特定领域教材等场景。需求分析文档中将 **RAG 私有知识库** 列为 P1 优先级扩展功能——支持用户创建私有知识库，从中生成试题，适用于企业培训、考试复习、个人笔记等场景。

同时，后续需要构建 **AI Agent 知识库**（关于 AI Agent 框架、模式、工具的文档集），作为 Agentic RAG 的基础。但目前既没有系统内置知识库，也没有用户上传机制。本变更解决"知识从哪来"的核心问题。

**为什么现在做？** 用户系统（登录、个人中心、数据库）已搭建完毕，MySQL 已就绪，LLM 链路已成熟，Tavily 搜索已集成——RAG 基础设施所需的 Embedding + 向量检索是最后一个缺失的拼图。

**核心问题**：
1. 知识库的文档来源：AI 生成 vs 用户上传 vs 两者结合？
2. RAG 的技术选型：向量库选什么？Embedding 用哪个？检索策略怎么定？
3. 如何与现有出题链无缝集成？

## What Changes

本变更引入一套完整的 **RAG 私有知识库系统**，包含以下核心能力：

- **知识库管理**：用户可以创建/删除/管理多个私有知识库（类似文件夹），每个知识库包含多份文档
- **文档导入**：支持两种文档来源——
  - 用户上传文档（PDF、Word、TXT、Markdown）
  - 系统内置知识库（AI Agent 知识包，由预置文档组成）
- **文档解析与向量化**：自动解析文档内容，分块（Chunking）、Embedding 向量化、存入向量库
- **RAG 出题**：出题时从指定知识库检索相关内容，作为上下文注入 Prompt 生成题目
- **搜索策略融合**：支持仅知识库、仅网络搜索、知识库+网络搜索三种模式（为后续 Agentic RAG 铺路）

> 本变更**不包含** Agentic RAG（AI 自主决定查哪种方式），那是后续阶段。

## Capabilities

### New Capabilities
- `knowledge-base-crud`: 知识库的创建、列表、删除等管理功能
- `document-ingestion`: 文档导入（用户上传 PDF/Word + 系统内置知识包），文档解析（文本提取）、分块（Chunking）、向量化
- `rag-generation`: 基于 RAG 的出题功能——从指定知识库检索相关内容，注入 Prompt 生成题目。与现有搜索增强出题链并行，用户可选择知识库出题或搜索出题

### Modified Capabilities
- （无修改——search-augmented-quiz 作为独立能力保持不变，新增 rag-generation 并行方案）

## Impact

### 后端影响
| 模块 | 影响 |
|------|------|
| `app/services/` | 🆕 新增 `knowledge_service.py`（知识库管理）、`rag_service.py`（RAG 检索服务）、`document_service.py`（文档解析处理） |
| `app/chains/` | 🆕 新增 `rag_quiz_chain.py`（RAG 出题链）或扩展现有 `quiz_chain.py` |
| `app/prompts/` | 🆕 新增 `rag_quiz_prompt.py`（RAG 增强 Prompt 模板） |
| `app/models/` | 🆕 新增 `knowledge.py`（知识库相关 Pydantic 模型）；修改 `quiz.py` 支持知识库参数 |
| `app/api/` | 🆕 新增知识库/文档/RAG 出题 API 路由 |
| `requirements.txt` | 新增 Embedding + 向量库依赖 |

### 数据库影响
- 🆕 新增 `knowledge_bases` 表（知识库）
- 🆕 新增 `knowledge_documents` 表（文档元数据）
- 🆕 新增 `knowledge_chunks` 表（文档分块）
- 🆕 新增向量存储（Milvus/Chroma/Qdrant 之一，或 MySQL 向量插件）

### 前端影响
- 🆕 新增知识库管理页面
- 🆕 新增文档上传组件
- 🆕 出题页面新增"知识库选择"选项
- 🆕 提示内置知识库来源信息

### 依赖变更
| 依赖 | 用途 |
|------|------|
| `sentence-transformers` 或 `dashscope` | 文本 Embedding |
| `chromadb` 或 `pymilvus` 或 `qdrant-client` | 向量数据库 |
| `docling` 或 `unstructured` 或 `pdfminer` | 文档解析（PDF/Word） |
| `langchain-community` | 向量存储集成 |
