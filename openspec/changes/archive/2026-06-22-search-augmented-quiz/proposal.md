## Why

当前 AI 出题系统完全依赖 DeepSeek 模型的训练知识，模型训练数据有截止日期，无法覆盖最新知识。当用户输入"Harness Engineering"等较新或小众的概念时，模型可能给出错误题解或混淆为其他领域的知识。需求分析文档明确要求"AI 自动从全网获取知识补充"，这一核心环节目前完全缺失，必须补上。

## What Changes

- **新增 AI 自主搜索增强出题流程**：将 TavilySearch 和 TavilyExtract 两个工具直接提供给 AI，让 LLM 自主决定何时调用搜索、何时提取网页内容，以及使用什么参数（搜索深度、结果条数、时间范围等），根据搜索结果出题
- **集成 Tavily 搜索引擎**：通过 `langchain-tavily` 包接入 Tavily Search API（专为 AI Agent 设计的搜索引擎），替代原有的 DuckDuckGo 方案
- **支持两种输入场景**：
  - 用户输入关键词/知识点 → AI 自主调用 `TavilySearch` 搜索最新资料（动态调整 search_depth、max_results、time_range 等参数）
  - 用户输入网页 URL → AI 自主调用 `TavilyExtract` 提取整个页面的内容
- **不再提供前端开关**：搜索增强始终开启，不再由用户控制
- **修改出题链为 Agent 模式**：出题流程改为 Agent 驱动 — AI 先调用工具搜集资料，再基于资料生成题目
- **修改题目数据模型**：新增 `knowledgeSource` / `searchEnhanced` / `searchSources` 响应字段
- **搜索失败自动降级**：搜索失败或超时时静默降级为纯模型知识出题，记录 warning 日志

## Capabilities

### New Capabilities
- `search-augmented-quiz`: 搜索增强出题能力 — 将 TavilySearch 和 TavilyExtract 工具提供给 AI，让 AI 自主搜索最新资料后出题，确保题目内容的时效性和准确性

### Modified Capabilities
- （暂无现有 specs 需要修改）

## Impact

- **后端新增/替换文件**：
  - `app/services/search_service.py` — 搜索增强编排服务（直接使用 langchain-tavily 工具）
- **后端修改文件**：
  - `app/prompts/quiz_prompt.py` — 新增搜索增强专用 Prompt，指导 AI 如何使用工具以及基于搜索结果出题
  - `app/models/quiz.py` — 新增 `knowledgeSource`、`searchEnhanced`、`searchSources` 字段
  - `app/chains/quiz_chain.py` — 重构为 Agent 模式，绑定 TavilySearch + TavilyExtract 工具
  - `app/services/quiz_service.py` — 集成 Agent 驱动的搜索增强出题流程
  - `requirements.txt` — 新增 `langchain-tavily` 依赖（替代原有的 duckduckgo_search/beautifulsoup4/lxml）
  - `app/config.py` — 新增 `TAVILY_API_KEY` 配置
- **前端无变更**（不再需要开关 UI）
- **API 变更**：`POST /api/quiz/generate` 响应体新增 `knowledgeSource`/`searchEnhanced`/`searchSources` 字段（请求体无新增字段）
