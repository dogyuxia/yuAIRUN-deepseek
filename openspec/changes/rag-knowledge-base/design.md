## Context

### 当前状态
- 搜索增强出题（Tavily）已实现，AI Agent 可自主搜索互联网辅助出题
- 用户系统已搭建（MySQL + JWT + SQLAlchemy）
- 后端使用 FastAPI + LangChain + DeepSeek
- 前端使用 Taro 4 + React + TypeScript

### 为什么需要 RAG
| 场景 | 搜索增强（现有） | RAG 知识库（待建） |
|------|-----------------|-------------------|
| 公开知识（技术文档、最新新闻） | ✅ Tavily 搜索 | ❌ 不适用 |
| 私密知识（企业内部文档） | ❌ 搜不到 | ✅ RAG |
| 教材/考试资料 | ❌ 不精确 | ✅ RAG |
| AI Agent 知识包 | ❌ 无来源 | ✅ 系统内置 |

### 核心问题
1. **知识来源**：AI 生成 vs 用户上传 vs 两者结合？
2. **技术选型**：向量数据库、Embedding 模型、文档解析方案
3. **集成方式**：如何与现有出题链共存（搜索出题 / RAG 出题 / 混合出题）

## Goals / Non-Goals

**Goals:**
1. 提供一套完整的知识库管理能力（CRUD）
2. 支持两种文档导入方式：用户上传（PDF/Word/TXT/MD）和系统内置知识包
3. 文档自动解析、分块（Chunking）、向量化
4. 出题时支持从指定知识库检索相关内容
5. 与现有搜索增强出题链并存，用户可选择出题方式
6. 为后续 Agentic RAG（AI 自主选择检索方式）打好架构基础

**Non-Goals:**
1. ❌ Agentic RAG（AI 自主决定搜索/知识库/混合）—— 下一阶段
2. ❌ 文档在线预览/富文本编辑
3. ❌ 多租户/权限管理（初期简化）
4. ❌ 知识库自动更新/定时爬取
5. ❌ 分布式向量库部署（初期本地文件型即可）

## Decisions

### 决策 1：知识库文档来源方案评估

| 方案 | 优点 | 缺点 | 推荐 |
|:----:|------|------|:----:|
| **A: 仅 AI 生成** | 零人工成本，快速构建 | 质量不可控，可能含幻觉，缺少权威性 | ❌ |
| **B: 仅用户上传** | 内容真实，用户可控 | 冷启动无内容，用户上手门槛高 | ❌ |
| **C: 系统内置 + 用户上传** | 冷启动有内容，用户可扩展 | 需要维护内置知识包 | ✅ **推荐** |

**推荐方案 C：系统内置 + 用户上传**

分层策略：
```
        冷启动阶段                    成熟阶段
    ┌─────────────────┐         ┌─────────────────┐
    │  系统内置知识包    │         │  系统内置知识包    │
    │  (AI Agent方向)   │         │  (持续更新)       │
    └────────┬────────┘         └────────┬────────┘
             │                           │
    ┌────────▼────────┐         ┌────────▼────────┐
    │  用户上传文档     │         │  用户上传文档     │
    │  (数量较少)       │         │  (逐渐增多)      │
    └─────────────────┘         └─────────────────┘
```

**系统内置知识包（第一阶段）**：聚焦 AI Agent 方向
- AI Agent 核心概念与框架（LangChain、LangGraph、CrewAI 等）
- 常用 Agent 模式（ReAct、Plan-and-Execute、Tool-use）
- 最佳实践与设计模式
- 来源：由开发者整理权威资料，或 AI 辅助生成+人工审核

**用户上传（第一阶段）**：
- 支持 PDF、Word（.docx）、TXT、Markdown
- 单文件限制 ≤ 20MB
- 每知识库最多 50 份文档

---

### 决策 2：向量数据库选型

| 维度 | **ChromaDB** | **Milvus** | **Qdrant** | **PGVector** |
|------|:-----------:|:----------:|:----------:|:------------:|
| 部署复杂度 | ⭐⭐⭐ 极简（文件型） | ⭐ 复杂（需 Docker） | ⭐⭐ 中等 | ⭐⭐ 需 PostgreSQL |
| 与 LangChain 集成 | ✅ 原生支持 | ✅ 原生支持 | ✅ 原生支持 | ✅ 原生支持 |
| 适合中文 Embedding | ✅ | ✅ | ✅ | ✅ |
| 性能（百万级向量） | 中等 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| 持久化 | 本地文件 | 独立服务 | 独立服务 | PostgreSQL |
| MVP 友好度 | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |

**推荐：ChromaDB**（PersistentClient 模式）

**理由：**
1. **零运维**：本地文件持久化，无需 Docker/独立服务，和 SQLite 一样简单
2. **MVP 阶段足够**：少量知识库文档，向量规模在千级，ChromaDB 性能绰绰有余
3. **LangChain 原生集成**：`langchain-chroma` 包开箱即用
4. **渐进式升级**：未来量大了可平滑迁移到 Milvus/Qdrant，接口兼容

```python
# ChromaDB PersistentClient — MVP 最佳选择
import chromadb

client = chromadb.PersistentClient(path="./chroma_data")
collection = client.get_or_create_collection(name="knowledge_base")
```

---

### 决策 3：Embedding 模型选型

| 模型 | 维度 | 中文能力 | 费用 | 推荐场景 |
|------|:----:|:--------:|:----:|---------|
| **BGE-M3 (BAAI/bge-m3)** | 1024 | ✅✅✅ 优秀 | 免费（本地） | **🏆 首选**：中英双语，开源免费 |
| **BGE-large-zh-v1.5** | 1024 | ✅✅✅ 优秀 | 免费（本地） | 纯中文场景替代方案 |
| **text-embedding-3-small** | 1536 | ✅✅ 良好 | 付费（OpenAI） | 已有 OpenAI 订阅 |
| **DeepSeek Embedding** | 待确认 | ✅✅✅ | 付费 | 若 DeepSeek 推出 |
| **M3E (moka-ai/m3e-base)** | 768 | ✅✅✅ 优秀 | 免费（本地） | 国产轻量方案 |

**推荐：BGE-M3 (BAAI/bge-m3)**

**理由：**
1. 中英双语能力顶级，适合技术文档（大量英文术语+中文解释）
2. 1024 维度平衡了精度和存储
3. 开源免费，本地运行，无 API 调用成本
4. 支持稠密检索（Dense Retrieval）和稀疏检索（Sparse Retrieval）
5. 通过 `sentence-transformers` 或 `HuggingFaceEmbeddings` 集成

```python
from langchain_huggingface import HuggingFaceEmbeddings

embeddings = HuggingFaceEmbeddings(
    model_name="BAAI/bge-m3",
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)
```

> **注意**：BGE-M3 约 2.2GB，首次运行需下载。如觉得太大，可选 M3E（~500MB）作为轻量替代。

---

### 决策 4：文档解析方案

| 方案 | 支持格式 | 中文支持 | 复杂度 |
|------|---------|:--------:|:------:|
| **Docling** | PDF, DOCX, PPTX, HTML, Images | ✅✅✅ | 低 |
| **Unstructured** | PDF, DOCX, HTML, Email, 图片 | ✅✅ | 中 |
| **PyMuPDF + python-docx** | PDF, DOCX | ✅✅ | 高（手写逻辑） |

**推荐：Docling**

**理由：**
1. **IBM 开源**，专为 AI 文档处理设计
2. 有官方的 `langchain-docling` 集成（`DoclingLoader`），与 LangChain 无缝对接
3. 支持 PDF（含表格）、DOCX、PPTX、HTML、图片
4. 内置 HybridChunker，自动按语义分块
5. 中文 PDF 解析效果优秀

```python
from langchain_docling import DoclingLoader
from docling.chunking import HybridChunker

loader = DoclingLoader(
    file_path="用户上传的文档.pdf",
    chunker=HybridChunker(
        tokenizer=HuggingFaceTokenizer.from_pretrained("BAAI/bge-m3"),
    ),
)
docs = loader.load()  # 返回 LangChain Document 列表，可直接入库
```

---

### 决策 5：分块策略 (Chunking)

| 策略 | 块大小 | 重叠 | 适用场景 |
|------|:------:|:----:|---------|
| **HybridChunker（Docling）** | 自动 | 自动 | 有 Docling 解析的文档 |
| **RecursiveCharacterTextSplitter** | 500~1000 tokens | 100~200 | 通用文本 |
| **MarkdownHeaderTextSplitter** | 按标题 | 按标题层级 | Markdown 结构文档 |

**推荐：HybridChunker（Docling 内置）+ RecursiveCharacterTextSplitter（兜底）**

对于 Docling 解析的文档，使用 HybridChunker（按文档结构+语义分块）。
对于纯文本，使用 RecursiveCharacterTextSplitter（chunk_size=500, chunk_overlap=100）。

---

### 决策 6：RAG 出题与现有出题链的关系

```
                        ┌──────────────────┐
                        │   用户输入 Topic   │
                        └────────┬─────────┘
                                 │
                        ┌────────▼─────────┐
                        │  选择出题方式     │
                        │  ┌─────────────┐ │
                        │  │ ① AI 搜索   │ │
                        │  │ ② 知识库    │ │
                        │  │ ③ 混合模式  │ │
                        │  └─────────────┘ │
                        └────────┬─────────┘
                                 │
                 ┌───────────────┼───────────────┐
                 ▼               ▼               ▼
        ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
        │ Tavily Search │ │ 向量检索      │ │ Search + RAG │
        │ (现有)        │ │ (ChromaDB)   │ │ (融合结果)    │
        └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
               │                │                │
               ▼                ▼                ▼
        ┌──────────────────────────────────────────┐
        │     DeepSeek 出题（基于检索到的上下文）     │
        │     with_structured_output               │
        └──────────────────────────────────────────┘
```

**三种模式并行存在，用户可选择**：
1. **AI 搜索出题**（现有）：Tavily 搜索 → 出题
2. **知识库出题**（新增）：ChromaDB 检索 → 出题
3. **混合模式**（新增）：Tavily + ChromaDB → 融合上下文 → 出题

> 这三种模式为后续 **Agentic RAG** 奠定基础——AI 自主判断用哪种方式。

---

### 决策 7：数据结构设计

#### 新增表

```sql
-- 知识库表
CREATE TABLE knowledge_bases (
    id VARCHAR(32) PRIMARY KEY COMMENT '知识库ID，格式 kb_xxx',
    user_id VARCHAR(32) NOT NULL COMMENT '所属用户ID（系统知识库 user_id = 'system'）',
    name VARCHAR(128) NOT NULL COMMENT '知识库名称',
    description VARCHAR(512) DEFAULT '' COMMENT '知识库描述',
    is_system TINYINT(1) NOT NULL DEFAULT 0 COMMENT '是否为系统内置知识库',
    doc_count INT NOT NULL DEFAULT 0 COMMENT '文档数量',
    chunk_count INT NOT NULL DEFAULT 0 COMMENT '分块数量',
    created_at DATETIME NOT NULL COMMENT '创建时间',
    updated_at DATETIME NOT NULL COMMENT '更新时间',
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_user (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 知识库文档表（元数据）
CREATE TABLE knowledge_documents (
    id VARCHAR(32) PRIMARY KEY COMMENT '文档ID，格式 kd_xxx',
    kb_id VARCHAR(32) NOT NULL COMMENT '所属知识库ID',
    user_id VARCHAR(32) NOT NULL COMMENT '上传用户ID',
    filename VARCHAR(256) NOT NULL COMMENT '原始文件名',
    file_type VARCHAR(16) NOT NULL COMMENT '文件类型: pdf/docx/txt/md',
    file_size INT NOT NULL DEFAULT 0 COMMENT '文件大小（字节）',
    file_path VARCHAR(512) NOT NULL COMMENT '文件存储路径',
    page_count INT DEFAULT NULL COMMENT '页数（PDF）',
    char_count INT NOT NULL DEFAULT 0 COMMENT '字符数',
    chunk_count INT NOT NULL DEFAULT 0 COMMENT '分块数',
    status VARCHAR(16) NOT NULL DEFAULT 'pending' COMMENT '状态: pending/processing/ready/failed',
    error_msg VARCHAR(512) DEFAULT NULL COMMENT '处理失败原因',
    created_at DATETIME NOT NULL COMMENT '上传时间',
    updated_at DATETIME NOT NULL COMMENT '更新时间',
    FOREIGN KEY (kb_id) REFERENCES knowledge_bases(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_kb (kb_id),
    INDEX idx_user (user_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

#### ChromaDB 文档结构

每份文档分块后，存入 ChromaDB Collection：

| ChromaDB 字段 | 值 |
|:-------------:|----|
| **id** | `kd_{doc_id}_chunk_{index}` |
| **document** | 分块文本内容 |
| **embedding** | BGE-M3 向量（1024维） |
| **metadata** | `{ kb_id, doc_id, filename, chunk_index, page_num? }` |

#### 知识库-出题 API

```json
// POST /api/quiz/generate 新增字段
{
  "subject": "AI Agent",
  "topic": "ReAct Pattern",
  "count": 5,
  "difficulty": "medium",
  "type": "single",
  "knowledgeBaseId": "kb_001",   // 🆕 指定知识库ID（为空则使用搜索增强）
  "searchMode": "knowledge_base"  // 🆕 "search" | "knowledge_base" | "hybrid"
}
```

---

### 决策 8：文件存储方案

| 方案 | 优点 | 缺点 | 推荐 |
|:----:|------|------|:----:|
| 本地文件系统 | 简单直接 | 不便于扩展，备份麻烦 | ✅ MVP |
| 云存储 OSS | 可靠、可扩展 | 需云服务，增加复杂度 | ❌ 后期 |

**MVP 采用本地文件系统**：`./uploads/knowledge/{kb_id}/{doc_id}.{ext}`

---

### 决策 9：系统内置知识包的构建方式

| 方案 | 优点 | 缺点 | 推荐 |
|:----:|------|------|:----:|
| **纯 AI 生成** | 快速、覆盖面广 | 质量不可控，可能含幻觉 | ❌ |
| **开发者整理** | 质量可控，权威 | 耗时，需要领域知识 | ✅ 核心部分 |
| **AI 生成 + 人工审核** | 效率+质量兼顾 | 仍需人工投入 | ✅ **推荐** |

**推荐方案**：AI 生成初稿 → 开发者人工审核/修正 → 定稿入库

**第一阶段内置知识包内容（AI Agent 方向）**：

| 知识包 | 内容范围 | 文档数 |
|--------|---------|:------:|
| AI Agent 基础概念 | Agent 定义、类型、应用场景 | 3~5 |
| LangChain 框架 | Chain、Agent、Tool、Memory 等核心概念 | 5~8 |
| Agent 设计模式 | ReAct、Plan-and-Execute、Tool-use、Multi-agent | 5~8 |
| Prompt Engineering | 提示工程技巧、Few-shot、Chain-of-Thought | 3~5 |
| RAG 技术 | 向量检索、Embedding、Chunking 策略 | 3~5 |
| AI Agent 评估 | 评估方法、基准测试、最佳实践 | 2~3 |

> 这些 Markdown 文档存放在 `backend/knowledge_base/default/` 目录下。

---

### 决策 10：文档处理架构

```
用户上传文档 / 系统知识包
        │
        ▼
┌──────────────────┐
│ 1. 保存原始文件   │ ← 存入 uploads/{kb_id}/{doc_id}.ext
└────────┬─────────┘
        │
        ▼
┌──────────────────┐
│ 2. Docling 解析   │ ← 提取纯文本 + 表格 + 结构
└────────┬─────────┘
        │
        ▼
┌──────────────────┐
│ 3. HybridChunker  │ ← 按语义分块
└────────┬─────────┘
        │
        ▼
┌──────────────────┐
│ 4. BGE-M3 Embed   │ ← 每块生成 1024 维向量
└────────┬─────────┘
        │
        ▼
┌──────────────────┐
│ 5. 存入 ChromaDB  │ ← 索引完成
│    更新 MySQL     │ ← 更新文档状态
└──────────────────┘
```

**异步处理**：文档上传后，使用后台任务（FastAPI BackgroundTasks）异步处理，避免阻塞 API 响应。

---

### 决策 11：新增 API 接口

| 方法 | 路径 | 说明 | 认证 |
|:----:|------|------|:----:|
| `POST` | `/api/knowledge/base` | 创建知识库 | ✅ |
| `GET` | `/api/knowledge/bases` | 获取知识库列表（含系统知识库） | ✅ |
| `DELETE` | `/api/knowledge/base/{id}` | 删除知识库 | ✅ |
| `POST` | `/api/knowledge/base/{id}/documents` | 上传文档到知识库 | ✅ |
| `GET` | `/api/knowledge/base/{id}/documents` | 获取知识库文档列表 | ✅ |
| `DELETE` | `/api/knowledge/document/{id}` | 删除某份文档 | ✅ |
| `POST` | `/api/knowledge/base/{id}/reindex` | 重新索引知识库 | ✅ |

---

### 决策 12：所有出题链统一使用 `with_structured_output`

**背景**：当前所有出题链（传统链、搜索增强 Agent 链）的最终输出都使用手写 `parse_json_response()` 做正则解析，存在解析失败风险。RAG 出题链是新代码，应直接使用正确方案，并顺手修复旧链。

**分析**：

| 维度 | 当前方案（正则解析） | 推荐方案（with_structured_output） |
|:----:|:-------------------:|:----------------------------------:|
| **输出合规率** | ~95%（极端情况可能失败） | ~100%（LLM 直接输出 Pydantic 模型） |
| **代码复杂度** | 30+ 行正则+兜底逻辑 | 1 行 `.with_structured_output(QuizResponse)` |
| **维护成本** | 高（JSON 格式变化需改正则） | 低（改 Pydantic 模型即可） |
| **与 LangChain 集成** | 手动 | 原生 |
| **DeepSeek 支持** | 不依赖 | ✅ 已确认支持 function calling |

```python
# 当前方案
chain = prompt | llm
result = await chain.ainvoke(inputs)
parsed = parse_json_response(result.content)  # 正则手写，有风险

# 推荐方案
structured_llm = llm.with_structured_output(QuizResponse)
result: QuizResponse = await structured_llm.ainvoke(prompt)
```

**受影响的链**（共 3 条）：
1. **RAG 出题链**（新写）→ 直接用 `with_structured_output`
2. **传统出题链** `QuizChain`（现有）→ 升级为 `with_structured_output`
3. **搜索增强 Agent 链** `SearchAugmentedQuizChain`（现有）→ 最终输出升级为 `with_structured_output`

**保留 `parse_json_response` 作为降级**：`with_structured_output` 失败时 fallback 到手动解析。

---

## Risks / Trade-offs

| 风险 | 影响 | 缓解措施 |
|------|:----:|---------|
| **ChromaDB 规模瓶颈** | 百万级向量性能下降 | MVP 阶段文档量远不到百万级；未来可迁移至 Milvus/Qdrant |
| **BGE-M3 模型体积大** | 首次下载 2.2GB，内存占用 ~4GB | 提供 M3E 作为轻量替代方案（~500MB）；使用模型缓存 |
| **文档解析失败** | 部分 PDF/Word 无法解析 | Docling 有良好的容错性；捕获异常标记状态为 failed |
| **中文 Embedding 质量** | 中英文混杂文档检索不准 | BGE-M3 中英双语 SOTA；可针对特定知识包调优 chunk_size |
| **用户上传恶意文件** | 安全风险 | 限制文件类型和大小；使用病毒扫描（后续）；沙箱解析 |
| **出题质量下降** | RAG 检索到无关上下文 | 使用 Hybrid Search（向量+关键词）；设置相似度阈值 |
| **存储膨胀** | 上传文件 + ChromaDB 占用磁盘 | 限制每用户知识库数量（10 个）；单文件 ≤ 20MB |

## 分阶段实施建议

```
Phase 1（当前变更）       Phase 2（下一阶段）
─────────────────────    ─────────────────────
✅ 系统内置知识包          🔲 Agentic RAG
✅ 用户上传文档（PDF等）    🔲 知识库分享
✅ ChromaDB + BGE-M3     🔲 文档预览/编辑
✅ 知识库 CRUD            🔲 智能知识包推荐
✅ RAG 出题链             🔲 全文检索+向量检索混合
✅ docx/txt/md 解析       🔲 分布式向量库
✅ 与搜索出题并存          🔲 知识库版本管理
```

## Open Questions

1. **系统内置知识包的内容**：AI Agent 方向的具体文档列表需要确认——是由我来生成初稿，还是你已有资料？
2. **用户上传的格式优先级**：是否只需要 PDF 和 Word，还是也需要 TXT、MD？
3. **知识库数量限制**：每个用户最多创建几个知识库？建议初期 10 个以内。
4. **出题页面 UI**：RAG 出题时需要让用户选择"知识库"，这个 UI 交互你已有想法还是需要设计？
