## Why

当前系统虽然支持三种出题策略（AI搜索、知识库、混合模式），但需要用户在界面上手动选择。这不仅增加了用户认知负担，而且没有发挥 AI 的自主决策能力——用户往往不清楚哪种模式最适合自己的学习内容。例如，学习热门技术（如"React Server Components"）应优先联网搜索，而学习已上传到知识库的内部材料（如"公司入职培训资料"）应优先检索知识库。我们应当让 AI 根据用户的输入内容自主判断并选择最优策略，实现 **Agentic RAG**（AI 自主判断检索方式）。

## What Changes

1. **Agentic RAG 核心机制**：不再让用户手动选择搜索模式（search/knowledge_base/hybrid），而是由 AI Agent 自主分析用户输入的 topic，判断最适合的检索策略——联网搜索、知识库检索、或两者混合，并动态决定检索参数（搜索深度、结果数量等）。
2. **题目标签系统**：每道题根据其知识来源自动打上标签：
   - 🤖 **AI 出题**：来自联网搜索或模型自身知识（`knowledgeSource: "web_search"` 或 `"model_knowledge"`）
   - 📚 **知识库题目**：来自私有知识库（`knowledgeSource: "knowledge_base"`）
3. **简化前端交互**：移除搜索模式选择器（search/knowledge_base/hybrid 三个按钮），用户只需选择知识库（或不选），AI 自动决定检索方式。用户选择知识库后，AI 会优先从知识库检索，并根据需要补充联网搜索。
4. **后端路由重构**：`quiz_service.py` 中不再按 `searchMode` 硬路由，而是由统一的 AgenticQuizChain 自主决策。兼容旧接口参数（`searchMode` 不再用于判断，仅作为提示）。
5. **新增前端题型来源显示**：在答题页面中每道题显示来源标签（"AI 出题"或"知识库题目"），增加用户信任感。

## Capabilities

### New Capabilities
- `agentic-quiz-strategy`: AI 自主判断检索方式的出题策略——AI Agent 分析用户输入，决定联网搜索、知识库检索还是混合检索，动态设置检索参数，最终生成带来源标签的题目。

### Modified Capabilities
- `search-augmented-quiz`: 现有一对一搜索模式（search/knowledge_base/hybrid）由用户选择，变更为 AI 自主决策。原有 `searchMode` 参数废弃，新增 AI 自主决策逻辑。题目的 `knowledgeSource` 字段语义扩展，前端展示为中文标签。

## Impact

- **后端**：
  - `app/chains/quiz_chain.py` — 新增 `AgenticQuizChain` 类，整合 Tavily 搜索、Tavily 提取和 ChromaDB 知识库检索
  - `app/chains/rag_quiz_chain.py` — 修改 `RAGQuizChain`，支持作为 Agent 的子工具调用
  - `app/services/quiz_service.py` — 重构 `generate_quiz()` 路由逻辑，废除 `searchMode` 硬路由
  - `app/models/quiz.py` — 扩展 `knowledgeSource` 字段映射逻辑
  - `app/prompts/quiz_prompt.py` — 新增 Agent 驱动 Prompt，整合知识库和网络搜索
  - `app/prompts/rag_quiz_prompt.py` — 调整 Prompt 以支持标签系统
- **前端**：
  - `src/components/KnowledgeBaseSelector/index.tsx` — 移除搜索模式选择（三个 chip），仅保留知识库选择
  - `src/pages/topic-input/index.tsx` — 移除 `searchMode` 相关状态和 UI
  - `src/types/quiz.ts` — 扩展 `KnowledgeSource` 类型，新增标签展示字段
  - `src/types/knowledge.ts` — 移除 `SearchMode` 类型或标记为废弃
  - `src/components/QuizCard/index.tsx` — 新增"AI 出题"和"知识库题目"标签展示
- **API**：
  - `POST /api/quiz/generate` — `searchMode` 参数不再作为路由判断依据（向后兼容）
- **依赖**：无新增依赖
