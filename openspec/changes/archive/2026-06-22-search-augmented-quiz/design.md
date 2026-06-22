## Context

当前出题流程：用户输入 Topic → DeepSeek 直接出题（纯依赖模型训练知识）。问题在于模型训练数据有截止日期，无法覆盖最新知识，存在知识混淆风险。

需求分析文档明确要求"AI 自动从全网获取知识补充"，但当前实现完全缺失这一环节。

用户可能输入两种类型的内容：
1. **关键词/知识点描述**（如"Harness Engineering"）— 需要搜索相关资料
2. **网页 URL**（如某篇最新论文的链接）— 需要提取整个页面的内容

## Goals / Non-Goals

**Goals:**
- 将 TavilySearch 和 TavilyExtract 工具提供给 AI，让 AI 自主决定搜索策略
- AI 能识别用户输入是关键词还是 URL，动态选择合适的工具
- AI 能根据知识复杂度动态调整搜索参数（search_depth、max_results、time_range 等）
- 搜索失败时自动降级，记录 warning 日志，用户无感知
- 搜索增强始终开启，不提供前端开关

**Non-Goals:**
- 不引入向量数据库，不使用传统 RAG 方案（属于 Phase 2 扩展功能）
- 不改变现有的题目类型、答题流程、报告生成等核心逻辑
- 不提供前端"联网搜索增强"开关（搜索始终开启）
- 不维护自己的网页抓取逻辑（TavilyExtract 负责内容提取）

## Decisions

| 决策 | 选择 | 替代方案 | 理由 |
|------|------|---------|------|
| 搜索引擎 | Tavily (langchain-tavily) | DuckDuckGo、Bing API | 专为 AI Agent 设计，直接返回结构化结果；LangChain 官方集成包，API 设计友好；每月 1000 次免费搜索额度 |
| 内容提取 | TavilyExtract (langchain-tavily) | BeautifulSoup 自建抓取 | 同一包无需额外依赖；支持 basic/advanced 两种提取深度；自动处理反爬、JS 渲染等复杂场景 |
| 输入判断方式 | AI Agent 自主判断 | 后端正则判断 URL | 更灵活，AI 能根据上下文选择最佳策略；如需 URL 可调用 TavilyExtract，如需搜索可调用 TavilySearch |
| 搜索参数控制 | AI 动态决定 | 后端硬编码固定参数 | TavilySearch 的 search_depth、max_results、time_range、include_domains 等参数均可由 AI 在调用时动态设置，适应不同场景 |
| 出题架构 | Agent 模式（工具 + LLM） | Chain 模式（固定 Pipeline） | Agent 可以在生成题目之前自主决定搜索策略，Chain 模式无法灵活响应不同输入类型 |
| 降级策略 | 搜索失败时降级 + warning 日志 | 提示用户重试 | 用户无感知，保障核心出题流程不中断 |
| 国内/国际兼顾 | AI 动态调整地域参数 | 固定英文搜索 | AI 可以根据 Topic 语言/上下文决定搜索策略，如中文内容自动调整 |
| 前端开关 | 不提供（始终开启） | 提供 Switch 开关 | 简化用户体验，搜索增强是后台能力，不需要用户理解或控制 |

## Risks / Trade-offs

| 风险 | 影响 | 概率 | 应对策略 |
|------|------|------|---------|
| Tavily API Key 耗尽免费额度 | 搜索增强不可用 | 低（月 1000 次） | 自动降级为纯模型知识出题；监控使用量 |
| Tavily 搜索结果不相关 | 出题质量无提升 | 低 | AI 可在 Prompt 中被指导评估搜索结果质量，低质量时可结合自身知识 |
| TavilyExtract 提取失败 | URL 内容无法获取 | 低 | AI 降级为用 TavilySearch 搜索该 URL 相关的摘要信息 |
| Agent 工具调用超时 | 整体响应延迟 | 中 | 设置合理的工具调用超时（如 15s），超时后降级 |
| DeepSeek 不支持工具调用 | Agent 模式不可用 | 低 | DeepSeek API 兼容 OpenAI 格式，支持 function calling |
