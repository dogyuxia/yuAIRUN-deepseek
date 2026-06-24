# RAG 技术概述

## 什么是 RAG？

RAG（Retrieval-Augmented Generation，检索增强生成）是一种将**信息检索**与**文本生成**相结合的 AI 技术。它在 LLM 生成答案之前，先从知识库中检索相关内容，然后将检索到的内容作为上下文注入 Prompt。

## 为什么需要 RAG？

| 问题 | 纯 LLM 的局限 | RAG 的解决方案 |
|------|--------------|---------------|
| **知识截止** | 训练数据有截止日期 | 实时检索最新知识 |
| **私有知识** | LLM 不知道企业内部数据 | 检索企业私有知识库 |
| **幻觉** | 可能编造不存在的"事实" | 基于检索到的资料回答 |
| **可追溯** | 不知道信息来源 | 可标注引用来源 |

## RAG 的核心流程

```
用户查询
    │
    ▼
┌──────────────────┐
│ 1. 检索阶段       │
│ 查询向量化         │
│ → 向量相似度搜索   │
│ → 返回 Top-K 文档  │
└────────┬─────────┘
         │ 检索到的相关文档
         ▼
┌──────────────────┐
│ 2. 增强阶段       │
│ 检索结果 + 原始查询 │
│ → 组装增强 Prompt  │
└────────┬─────────┘
         │ 增强后的 Prompt
         ▼
┌──────────────────┐
│ 3. 生成阶段       │
│ LLM 基于上下文     │
│ → 生成最终回答     │
└────────┬─────────┘
         │
         ▼
      输出
```

## RAG 的关键组件

### 1. 文档加载（Document Loading）

从各种来源加载文档：

```python
# 使用 Docling 加载 PDF
from langchain_docling import DoclingLoader

loader = DoclingLoader(file_path="document.pdf")
docs = loader.load()
```

### 2. 文本分割（Text Splitting）

将长文档分割为可检索的块：

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,      # 每块大小
    chunk_overlap=100,   # 重叠大小
)
chunks = splitter.split_documents(docs)
```

### 3. 向量化（Embedding）

将文本转为向量：

```python
from langchain_huggingface import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-m3",
    encode_kwargs={"normalize_embeddings": True},
)
```

### 4. 向量存储（Vector Store）

存储向量并支持相似度搜索：

```python
from langchain_chroma import Chroma

vector_store = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    collection_name="my_knowledge_base",
    persist_directory="./chroma_db",
)
```

### 5. 检索器（Retriever）

从向量库中检索相关文档：

```python
retriever = vector_store.as_retriever(
    search_type="similarity",  # 或 "mmr"（最大边际相关性）
    search_kwargs={"k": 5},   # 返回 Top-5
)
```

### 6. 生成（Generation）

将检索结果注入 Prompt，生成最终回答：

```python
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_template("""
基于以下资料回答问题：

资料：
{context}

问题：{question}

回答：
""")

chain = prompt | llm
result = chain.invoke({
    "context": "\n\n".join([d.page_content for d in retrieved_docs]),
    "question": query,
})
```

## RAG 的检索策略

### 1. 简单相似度搜索

```python
retriever = vector_store.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 5},
)
```

### 2. MMR（最大边际相关性）

在相关性和多样性之间做平衡：

```python
retriever = vector_store.as_retriever(
    search_type="mmr",
    search_kwargs={"k": 5, "fetch_k": 20, "lambda_mult": 0.5},
)
```

### 3. 多查询检索

生成多个查询变体，提高召回率：

```python
from langchain.retrievers.multi_query import MultiQueryRetriever

retriever = MultiQueryRetriever.from_llm(
    retriever=base_retriever,
    llm=llm,
)
```

### 4. 上下文压缩

对检索结果进行压缩，只保留最相关的部分：

```python
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor

compressor = LLMChainExtractor.from_llm(llm)
compression_retriever = ContextualCompressionRetriever(
    base_compressor=compressor,
    base_retriever=base_retriever,
)
```

## RAG 的质量评估

| 指标 | 说明 | 优化方法 |
|:----:|------|---------|
| **召回率** | 检索到的相关文档占所有相关文档的比例 | 多查询、HyDE |
| **精确率** | 检索结果中相关文档的比例 | 调整相似度阈值 |
| **答案准确率** | 最终答案的正确性 | 优化 Prompt |
| **引用准确率** | 答案引用是否正确对应原文 | 块级别引用 |

## 高级 RAG 技术

### 1. HyDE（假设文档嵌入）

先用 LLM 生成一个"假设答案"，再用这个答案去检索：

```python
# 先生成假设文档
hypothetical_doc = llm.invoke(f"假设 '{query}' 的答案是：")
# 用假设文档去检索
results = vector_store.similarity_search(hypothetical_doc)
```

### 2. Self-RAG

让 LLM 自己判断是否需要检索，以及检索结果是否相关：

```python
# 1. 判断是否需要检索
if llm.should_retrieve(query):
    docs = retriever.get_relevant_documents(query)
    # 2. 判断每个文档是否相关
    relevant_docs = [d for d in docs if llm.is_relevant(d, query)]
    # 3. 基于相关文档回答
    answer = llm.answer_with_context(query, relevant_docs)
else:
    answer = llm.answer_without_context(query)
```

### 3. Agentic RAG

让 AI Agent 自主决定检索策略：
- 是否需要检索？
- 从哪个知识库检索？
- 要不要同时搜索互联网？
- 检索结果够不够用？

> 详见 Agent 设计模式相关文档。
