## 1. 基础依赖与配置

- [ ] 1.1 新增 Python 依赖到 `requirements.txt`（chromadb、langchain-chroma、langchain-huggingface、docling、langchain-docling）
- [ ] 1.2 安装依赖并验证可导入
- [ ] 1.3 在 `.env` 中新增 Embedding 模型缓存路径配置
- [ ] 1.4 创建 `backend/knowledge_base/default/` 目录结构

## 2. 数据库与模型层

- [ ] 2.1 创建 `app/db/models/knowledge_base.py` — `KnowledgeBaseModel` ORM 模型
- [ ] 2.2 创建 `app/db/models/knowledge_document.py` — `KnowledgeDocumentModel` ORM 模型
- [ ] 2.3 更新 `app/db/models/__init__.py` — 导出新模型
- [ ] 2.4 在 `app/models/` 下新增 `knowledge.py` — 知识库/文档的 Pydantic 请求/响应模型
- [ ] 2.5 在 `app/models/quiz.py` 的请求体中新增 `knowledgeBaseId` 和 `searchMode` 字段

## 3. 向量存储与 Embedding 服务

- [ ] 3.1 创建 `app/services/vector_service.py` — ChromaDB 客户端封装（初始化集合、添加/删除/查询向量）
- [ ] 3.2 创建 `app/services/embedding_service.py` — BGE-M3 Embedding 模型初始化与调用封装
- [ ] 3.3 创建 `app/services/document_processor.py` — Docling 文档解析 + HybridChunker 分块 + Embedding 入库的完整流程

## 4. 知识库管理 API

- [ ] 4.1 在 `app/api/v1/endpoints/` 下创建 `knowledge.py` — 知识库 CRUD 路由（创建、列表、删除）
- [ ] 4.2 在 `app/api/v1/endpoints/` 下创建 `document.py` — 文档上传、列表、删除、状态查询路由
- [ ] 4.3 更新 `app/main.py` — 注册新路由

## 5. 知识库业务逻辑服务

- [ ] 5.1 创建 `app/services/knowledge_service.py` — 知识库 CRUD 业务逻辑（含系统知识库种子逻辑）
- [ ] 5.2 创建 `app/services/document_service.py` — 文档上传/删除业务逻辑（含文件存储路径管理）
- [ ] 5.3 实现系统知识库初始化逻辑（应用启动时检测并自动创建 "AI Agent 知识库"）

## 6. with_structured_output 统一升级

- [ ] 6.1 升级 `app/chains/quiz_chain.py` 中的 `QuizChain` — 使用 `with_structured_output(QuizResponse)` 替换手写 `parse_json_response`
- [ ] 6.2 升级 `app/chains/quiz_chain.py` 中的 `SearchAugmentedQuizChain` — 最终输出使用 `with_structured_output(QuizResponse)` 替换正则解析
- [ ] 6.3 保留 `parse_json_response` 作为 `with_structured_output` 失败时的降级兜底

## 7. RAG 出题链

- [ ] 7.1 创建 `app/prompts/rag_quiz_prompt.py` — RAG 出题专用 Prompt（强调基于知识库资料出题）
- [ ] 7.2 创建 `app/chains/rag_quiz_chain.py` — RAG 出题链（向量检索 → 上下文组装 → `with_structured_output` 出题）
- [ ] 7.3 修改 `app/services/quiz_service.py` — 新增 RAG/混合模式出题逻辑，根据 `searchMode` 分发到不同出题链
- [ ] 7.4 修改 `app/chains/quiz_chain.py` — 可选：扩展现有搜索增强 Agent 以支持 RAG

## 8. 系统内置知识包（AI Agent 方向）

- [ ] 7.1 创建 "AI Agent 基础概念" 知识文档（Markdown，3~5 篇）
- [ ] 7.2 创建 "LangChain 框架" 知识文档（Markdown，5~8 篇）
- [ ] 7.3 创建 "Agent 设计模式" 知识文档（Markdown，5~8 篇）
- [ ] 7.4 创建 "Prompt Engineering" 知识文档（Markdown，3~5 篇）
- [ ] 7.5 创建 "RAG 技术" 知识文档（Markdown，3~5 篇）
- [ ] 7.6 创建 "AI Agent 评估" 知识文档（Markdown，2~3 篇）

## 9. 前端 — 知识库管理页面

- [ ] 9.1 在 `src/types/` 下新增 `knowledge.ts` — 知识库/文档的 TypeScript 类型定义
- [ ] 9.2 在 `src/services/` 下创建 `knowledge.ts` — 知识库 API 封装
- [ ] 9.3 创建 `src/pages/knowledge/` 页面 — 知识库列表展示（含系统知识库标识）
- [ ] 9.4 创建 `src/pages/knowledge-detail/` 页面 — 知识库详情文档列表与上传入口

## 10. 前端 — 文档上传组件

- [ ] 10.1 实现文档上传组件（支持 PDF/DOCX/TXT/MD，文件大小校验，上传进度）
- [ ] 10.2 实现文档列表展示（文件名、类型、大小、处理状态、上传时间）
- [ ] 10.3 实现文档删除功能（含确认弹窗）

## 11. 前端 — 出题页面集成知识库选择

- [ ] 11.1 修改 `src/pages/topic-input/index.tsx` — 新增知识库选择器 UI 组件
- [ ] 11.2 实现知识库选择器：展示用户知识库列表，支持选择/取消
- [ ] 11.3 实现搜索模式选择：AI 搜索出题 / 仅知识库 / 混合模式
- [ ] 11.4 更新 `src/types/api.ts` — 请求体新增 `knowledgeBaseId` 和 `searchMode` 字段
- [ ] 11.5 更新 `src/services/quiz.ts` — 出题请求携带知识库参数

## 12. 测试与验证

- [ ] 12.1 编写知识库 CRUD API 测试
- [ ] 12.2 编写文档上传/解析/索引测试
- [ ] 12.3 编写 RAG 出题链测试（含 Mock 模式）
- [ ] 12.4 端到端验证：完整流程（上传文档 → 自动索引 → 知识库出题 → 答题）
- [ ] 12.5 验证 with_structured_output 降级：模拟失败时自动 fallback 到 parse_json_response
- [ ] 12.6 验证搜索降级：ChromaDB 不可用时自动降级为搜索出题
