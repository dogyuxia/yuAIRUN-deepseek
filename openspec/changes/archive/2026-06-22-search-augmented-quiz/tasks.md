## 1. 依赖安装与配置

- [x] 1.1 在 `requirements.txt` 中添加 `langchain-tavily` 依赖
- [x] 1.2 在 `app/config.py` 中新增 `TAVILY_API_KEY` 配置项（用户需在 `.env` 中配置 `TAVILY_API_KEY=你的key`）
- [x] 1.3 通过 Context7 或官方文档确认 `langchain-tavily` 的最新 API 用法

## 2. 数据模型修改

- [x] 2.1 修改 `app/models/quiz.py` — `QuizQuestion` 新增 `knowledgeSource` 字段（`Literal["web_search", "model_knowledge"]`）；`QuizMetadata` 新增 `searchEnhanced: bool` 和 `searchSources: list[str]` 字段
- [x] 2.2 修改 `yuairun-frontend/src/types/quiz.ts` — 同步更新前端类型定义

## 3. Prompt 模板修改

- [x] 3.1 修改 `app/prompts/quiz_prompt.py` — 新增搜索增强版本的 System Prompt，包含：
  - 工具使用指导：告知 AI 可使用 TavilySearch（搜索关键词）和 TavilyExtract（提取 URL 内容）
  - 参数动态选择指导：根据知识复杂度选择 search_depth、max_results、time_range 等
  - 国内/国际兼顾指导：根据 Topic 语言自动调整搜索策略
  - 出题要求：基于搜索结果出题，标注 knowledgeSource
  - 降级策略：搜索失败时使用模型自身知识

## 4. 出题链重构为 Agent 模式

- [x] 4.1 修改 `app/chains/quiz_chain.py` — 重构为 Agent 驱动模式：
  - 从 `langchain_tavily` 导入 `TavilySearch` 和 `TavilyExtract`
  - 实例化两个工具（设置合理的默认参数）
  - 使用 `langchain.agents.create_agent` 创建 Agent，绑定两个工具
  - Agent 流程：收到用户输入 → 自主决定调 TavilySearch/TavilyExtract → 基于收集材料生成题目
  - 设置工具调用超时保护（防止无限等待，失败时降级为传统链）

## 5. 服务层集成

- [x] 5.1 修改 `app/services/quiz_service.py` — 集成 Agent 驱动的出题链：
  - 不再需要 `enableSearch` 判断（始终开启）
  - 传入用户输入（可能为关键词或 URL）给 Agent
  - Agent 自主决定搜索策略
  - 设置合理的超时和错误处理
  - 搜索失败时记录 warning 日志并降级

## 6. 前端类型更新

- [x] 6.1 修改 `yuairun-frontend/src/types/quiz.ts` — `QuizQuestion` 新增 `knowledgeSource` 字段；`QuizMetadata` 新增 `searchEnhanced` 和 `searchSources` 字段
- [x] 6.2 确认前端 `topic-input` 页面无需任何 UI 变更（开关已移除）

## 7. 测试与验证

- [x] 7.1 测试场景一：输入关键词（如"Harness Engineering"），验证 AI 调用 TavilySearch 获取资料后出题
- [x] 7.2 测试场景二：输入 URL（如某篇最新论文链接），验证 AI 调用 TavilyExtract 提取内容后出题
- [x] 7.3 测试场景三：Tavily API 不可用时，验证降级为纯模型知识出题，记录 warning 日志
- [x] 7.4 验证响应中的 `knowledgeSource`、`searchEnhanced`、`searchSources` 字段正确填充
