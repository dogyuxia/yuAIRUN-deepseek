# Embedding 与向量数据库

## 什么是 Embedding？

Embedding（嵌入）是将**文本转换为数值向量**的过程。相似的文本在向量空间中距离更近，从而实现语义搜索。

### 工作原理

```
"猫"      → [0.12, 0.34, -0.56, ...]  ← 1024维向量
"狗"      → [0.11, 0.35, -0.55, ...]  ← 距离近（语义相似）
"计算机"  → [0.89, -0.23, 0.67, ...]  ← 距离远（语义不相似）
```

## 常用的 Embedding 模型

### BGE-M3 (BAAI/bge-m3)

| 属性 | 值 |
|------|------|
| **维度** | 1024 |
| **语言** | 中英双语 + 100+ 语言 |
| **大小** | ~2.2GB |
| **特点** | 支持稠密+稀疏检索，多语言表现优秀 |
| **许可证** | MIT（开源免费） |

```python
from langchain_huggingface import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-m3",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)
```

### M3E (moka-ai/m3e-base)

| 属性 | 值 |
|:----:|------|
| **维度** | 768 |
| **语言** | 中文为主 |
| **大小** | ~500MB |
| **特点** | 轻量，中文表现良好 |

### text-embedding-3-small (OpenAI)

| 属性 | 值 |
|:----:|------|
| **维度** | 1536（可降维） |
| **语言** | 多语言 |
| **费用** | 付费（按 token 计费） |
| **特点** | 质量高，但需 API 调用 |

## Embedding 模型选型指南

| 场景 | 推荐模型 |
|------|---------|
| 中英双语、技术文档 | BGE-M3 |
| 纯中文轻量需求 | M3E |
| 已有 OpenAI 订阅 | text-embedding-3-small |
| 资源受限设备 | M3E 或 bge-small |

## 什么是向量数据库？

向量数据库专门用于存储和检索向量（Embedding），支持高效的**近似最近邻搜索（ANN）**。

## 向量数据库对比

| 特性 | **ChromaDB** | **FAISS** | **Milvus** | **Qdrant** |
|:----:|:-----------:|:---------:|:----------:|:----------:|
| 部署方式 | 本地文件/内存 | 本地内存 | Docker 服务 | Docker 服务 |
| 持久化 | ✅ | ✅ 需手动 | ✅ | ✅ |
| 分布式 | ❌ | ❌ | ✅ | ✅ |
| 过滤 | ✅ 元数据过滤 | ❌ | ✅ 复杂过滤 | ✅ 复杂过滤 |
| 上手难度 | ⭐ 极低 | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 适合规模 | < 100万向量 | < 1000万 | 亿级 | 亿级 |

## ChromaDB 使用示例

### 初始化

```python
import chromadb

# 持久化模式（推荐）
client = chromadb.PersistentClient(path="./chroma_data")

# 内存模式（临时）
client = chromadb.Client()
```

### 创建/获取集合

```python
# 创建新集合
collection = client.create_collection(
    name="knowledge_base",
    metadata={"hnsw:space": "cosine"},  # 距离度量
)

# 获取已有集合
collection = client.get_collection("knowledge_base")

# 不存在则创建
collection = client.get_or_create_collection("knowledge_base")
```

### 添加文档

```python
collection.add(
    ids=["doc_1_chunk_0", "doc_1_chunk_1"],
    documents=["文本内容1", "文本内容2"],
    metadatas=[
        {"source": "doc_1", "page": 1},
        {"source": "doc_1", "page": 2},
    ],
    embeddings=[[0.1, 0.2, ...], [0.3, 0.4, ...]],  # 可选，不传则用默认 Embedding
)
```

### 查询

```python
results = collection.query(
    query_texts=["TCP 三次握手"],
    n_results=5,
    where={"source": "doc_1"},  # 可选过滤
    include=["documents", "distances", "metadatas"],
)
```

### 删除

```python
collection.delete(ids=["doc_1_chunk_0"])
collection.delete(where={"source": "doc_1"})  # 条件删除
```

## 使用 LangChain Chroma 集成

```python
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-m3")

# 创建向量库
vector_store = Chroma.from_documents(
    documents=chunks,
    embedding=embeddings,
    collection_name="my_knowledge_base",
    persist_directory="./chroma_db",
)

# 检索
retriever = vector_store.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 5},
)
results = retriever.invoke("TCP 三次握手")
```

## 相似度度量方式

| 度量 | 说明 | 适用场景 |
|:----:|------|---------|
| **余弦相似度** | 关注方向而非长度 | 文本相似度（最常用） |
| **欧氏距离** | 绝对距离 | 数值特征 |
| **点积** | 方向和长度的乘积 | 已归一化的向量 |

## Embedding 的最佳实践

1. **归一化**：`normalize_embeddings=True` 确保向量长度一致
2. **批次处理**：大量文档时分批 Embedding，避免内存溢出
3. **缓存模型**：首次加载后缓存模型，避免重复加载
4. **选择合适的维度**：维度越高越精确，但计算成本也越高
5. **定期重建索引**：增删文档后重建索引保持检索质量
