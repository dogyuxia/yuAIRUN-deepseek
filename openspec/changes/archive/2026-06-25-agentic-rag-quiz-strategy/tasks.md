## 1. 后端 — 知识库检索工具封装

- [x] 1.1 创建 `app/tools/kb_retriever.py`，封装 `KnowledgeBaseRetriever` LangChain Tool，包装 ChromaDB 的 `search_similar_chunks()` 调用
- [x] 1.2 在 `app/tools/__init__.py` 中导出新工具

## 2. 后端 — AgenticQuizChain 核心实现

- [x] 2.1 在 `app/chains/agentic_quiz_chain.py` 中新增 `AgenticQuizChain` 类，集成 TavilySearch、TavilyExtract、KnowledgeBaseRetriever 三个工具
- [x] 2.2 设计并实现 Agent System Prompt，包含决策引导逻辑（topic 分析 → 策略选择 → 工具调用 → 出题）
- [x] 2.3 实现 JSON 解析和降级逻辑（Agent 失败时回退到传统链）
- [x] 2.4 在 `app/chains/quiz_chain.py` 中新增 `create_agentic_quiz_chain()` 工厂函数

## 3. 后端 — Prompt 模板更新

- [x] 3.1 在 `app/prompts/quiz_prompt.py` 中新增 `AGENTIC_QUIZ_SYSTEM_PROMPT` 和 `AGENTIC_QUIZ_HUMAN_PROMPT`，指导 Agent 自主决策
- [x] 3.2 在 `app/prompts/rag_quiz_prompt.py` 中调整 Prompt，确保 `knowledgeSource` 语义覆盖 `knowledge_base` 来源

## 4. 后端 — 路由与服务重构

- [x] 4.1 修改 `app/services/quiz_service.py` 中的 `generate_quiz()` 函数：废弃 `searchMode` 路由逻辑，改为统一调用 `AgenticQuizChain`
- [x] 4.2 修改 `app/models/quiz.py` 中的 `GenerateQuizRequest`：`searchMode` 改为可选字段，默认 `"agentic"`；`knowledgeBaseId` 保持不变
- [x] 4.3 扩展 `QuizMetadata` 模型：新增 `retrievalStrategy`、`toolsInvoked`、`fallback` 字段
- [x] 4.4 修改 `app/models/quiz.py` 中的 `QuizQuestion`：扩展 `knowledgeSource` 类型支持 `"knowledge_base"` 值（验证已有）

## 5. 后端 — 测试与验证

- [x] 5.1 编写 `AgenticQuizChain` 单元测试：模拟各种工具返回值，验证决策逻辑
- [x] 5.2 编写降级测试：模拟工具失败，验证回退逻辑
- [x] 5.3 运行现有测试套件，确保向后兼容（77/77 测试通过）

## 6. 前端 — 移除搜索模式选择 UI

- [x] 6.1 修改 `src/components/KnowledgeBaseSelector/index.tsx`：移除三个搜索模式 chip，仅保留知识库选择列表
- [x] 6.2 修改 `src/pages/topic-input/index.tsx`：移除 `searchMode` 状态和 `onSelectMode` 关联逻辑
- [x] 6.3 修改 `src/types/knowledge.ts`：标记 `SearchMode` 类型为 `@deprecated`，或移除

## 7. 前端 — 题目标签展示

- [x] 7.1 修改 `src/types/quiz.ts`：扩展 `KnowledgeSource` 类型，加入 `"knowledge_base"`；新增 `knowledgeSourceLabel` 工具函数
- [x] 7.2 修改 `src/components/QuizCard/index.tsx`：根据 `knowledgeSource` 显示"🤖 AI 出题"或"📚 知识库题目"标签
- [x] 7.3 修改 `src/pages/quiz/index.tsx`（如需要）：确保标签在题目卡片中正确渲染（无改动需要，QuizCard 已自动处理）

## 8. 前后端联调与验收

- [ ] 8.1 联调测试：无知识库时出题（验证 Agent 走 web 搜索）— ⏳ 需要真实 Tavily API Key
- [ ] 8.2 联调测试：选择知识库后出题（验证 Agent 先走 KB 检索）— ⏳ 需要真实 API + ChromaDB 数据
- [ ] 8.3 联调测试：知识库内容不足时（验证 Agent 自动补充 web 搜索）— ⏳ 需要真实环境
- [ ] 8.4 验收：检查题目标签"🤖 AI 出题"和"📚 知识库题目"是否正确显示 — ✅ 代码已实现，需真机预览验证
- [x] 8.5 验收：检查旧 API 调用（携带 `searchMode` 参数）是否仍然正常工作 — ✅ 77/77 测试通过确认向后兼容
