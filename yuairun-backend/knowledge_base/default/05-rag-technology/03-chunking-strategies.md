# 分块策略（Chunking Strategies）

## 什么是 Chunking？

Chunking（分块）是将长文档**分割为若干较小的文本片段**的过程。每个片段（Chunk）会被独立向量化并存入向量库，供后续检索使用。

## 为什么 Chunking 很重要？

| 问题 | 块太大 | 块太小 |
|:----:|:------:|:------:|
| **检索精度** | 包含无关信息，噪声大 | 可能缺少上下文 |
| **语义完整性** | 一个块包含多个概念 | 一个概念被截断 |
| **Token 消耗** | 输送给 LLM 的上下文多 | 需要检索更多块 |
| **处理速度** | Embedding 慢 | Embedding 快但检索次数多 |

## 常见的分块策略

### 1. 固定大小分块（Fixed-size）

最简单的策略：按字符数或 token 数切分。

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,       # 每块 500 字符
    chunk_overlap=100,    # 重叠 100 字符（保持上下文连贯）
    separators=["\n\n", "\n", "。", ".", " ", ""],  # 优先在段落/句子处切分
    length_function=len,
)

chunks = splitter.split_documents(documents)
```

**优点**：简单、可控
**缺点**：可能切断语义完整的内容

### 2. 语义分块（Semantic Chunking）

基于内容的语义边界进行分割。

```python
from docling.chunking import HybridChunker
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer

chunker = HybridChunker(
    tokenizer=HuggingFaceTokenizer.from_pretrained("BAAI/bge-m3"),
    max_tokens=512,  # 每块最大 token 数
)

chunks = list(chunker.chunk(docling_document))
```

**优点**：保持语义完整
**缺点**：需要文档结构信息

### 3. 文档结构分块

基于 Markdown 标题、HTML 标签等结构分块。

```python
from langchain_text_splitters import MarkdownHeaderTextSplitter

splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=[
        ("#", "h1"),
        ("##", "h2"),
        ("###", "h3"),
    ],
)

chunks = splitter.split_text(markdown_document)
```

**优点**：结构清晰，易于理解
**缺点**：依赖文档有良好结构

### 4. 基于文档结构的分块（Docling Hybrid）

结合文档结构和语义，是目前最先进的方式。

```
文档结构：
# 标题
## 小节 1
段落 1 内容...
段落 2 内容...
## 小节 2
段落 3 内容...

HybridChunker 输出：
Chunk 1: "# 标题\n## 小节 1\n段落 1 内容...\n段落 2 内容..."
Chunk 2: "## 小节 2\n段落 3 内容..."
```

## 分块参数调优

### Chunk Size（块大小）

| 块大小 | 适用场景 | 检索粒度 |
|:------:|---------|:--------:|
| 128 tokens | 事实性问答（如"xx 是几月"） | 细粒度 |
| 256 tokens | | |
| **512 tokens** | **通用问答（推荐）** | **适中** |
| 1024 tokens | | |
| 2048 tokens | 摘要、综合分析 | 粗粒度 |

### Chunk Overlap（重叠大小）

| 重叠比例 | 效果 |
|:--------:|------|
| 0% | 可能丢失边界上下文 |
| **10~20%** | **推荐**，保持上下文连贯 |
| 30%+ | 冗余较多，浪费存储 |

## 分块策略选择指南

| 文档类型 | 推荐策略 | 原因 |
|---------|---------|------|
| Markdown 文档 | HybridChunker / MarkdownHeader | 利用标题结构 |
| PDF 论文 | Docling HybridChunker | 保持段落和章节完整 |
| HTML 页面 | RecursiveCharacter | 移除 HTML 标签后按文本分块 |
| 代码文件 | RecursiveCharacter | 按函数/类分块 |
| 纯文本 | RecursiveCharacter | 最简单的策略 |
| 混合格式 | Docling + HybridChunker | 通用方案 |

## 分块后的元数据

每个 Chunk 应该附带元数据，便于追溯和过滤：

```python
chunk_metadata = {
    "source": "document.pdf",    # 来源文档
    "chunk_index": 3,            # 块序号
    "total_chunks": 20,          # 总块数
    "page_number": 5,            # 页码（PDF）
    "section": "2.1 分块策略",   # 所在章节
    "kb_id": "kb_001",           # 所属知识库
    "doc_id": "kd_001",          # 所属文档
}
```

## 分块质量评估

| 指标 | 好 | 差 |
|:----:|:--:|:--:|
| **单块主题** | 单一主题 | 多个无关主题 |
| **上下文完整性** | 一句话/概念完整 | 句子被截断 |
| **信息密度** | 每个块包含有用的信息 | 大部分是停用词/格式 |
| **检索匹配度** | 查询能精确匹配 | 很难定位到相关内容 |

## 最佳实践

1. **优先使用 HybridChunker**：Docling 的语义分块效果最好
2. **块大小 500~1000 tokens**：大多数场景的甜点区间
3. **重叠 10~20%**：保证边界信息的连贯性
4. **保留文档结构**：元数据中包含标题、页码信息
5. **测试与调优**：用真实查询测试检索效果，调整参数
6. **考虑语言差异**：中文每 token 约 1.5 字符，英文约 4 字符
