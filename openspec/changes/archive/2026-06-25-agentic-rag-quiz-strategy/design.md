## Context

### 当前状态

系统已有三种出题模式，由用户在界面上手动选择：

| 模式 | 实现 | 用户操作 |
|------|------|---------|
| `search` | TavilySearch + TavilyExtract Agent | 用户选择"仅 AI 搜索" |
| `knowledge_base` | RAGQuizChain → ChromaDB | 用户选择"仅知识库" |
| `hybrid` | RAGQuizChain + SearchAugmentedQuizChain 合并 | 用户选择"混合模式" |

### 问题

1. **用户认知负担**：普通用户不理解"搜索模式"概念，不知道何时该选哪种
2. **决策次优**：用户无法判断哪种模式最适合当前 topic，往往选错
3. **效率低下**：`hybrid` 模式目前是串行调用两条链再合并，无法让 AI 动态调整策略
4. **缺乏透明度**：用户看到题目但不知道来源，影响对题目质量的信任感

### 技术约束

- DeepSeek API **不支持** OpenAI 的 `with_structured_output` / `response_format`，所有 JSON 输出通过 Prompt 引导 + 手动解析
- ChromaDB 作为向量数据库，通过 `search_similar_chunks()` 检索
- Tavily 工具通过 `langchain-tavily` 集成
- LangChain 的 `create_agent()` 支持绑定多个工具

## Goals / Non-Goals

**Goals:**
- AI Agent 自主分析用户 topic 并决定检索策略（搜索 web、检索 KB、或两者混合）
- 用户只需选择知识库（可选），不再手动选择搜索模式
- 每道题自动标注来源标签："AI 出题"或"知识库题目"
- 向后兼容现有的 API 接口（不破坏已有的前端调用）
- 保持或提升题目生成质量

**Non-Goals:**
- 不修改用户的登录、个人中心、报告等非出题相关模块
- 不修改知识库管理功能（创建、上传、删除等）
- 不引入新的外部依赖（复用现有的 Tavily + ChromaDB）
- 不修改数据库表结构
- 不处理多知识库同时检索（一次只选一个知识库）

## Decisions

### Decision 1: 单一 Agent 整合所有工具 vs 多 Agent 编排

**方案 A（选定）：单一 Agent + 多工具**

```
AgenticQuizChain (一个 Agent)
  ├── 工具: TavilySearch
  ├── 工具: TavilyExtract
  └── 工具: KnowledgeBaseRetriever (ChromaDB 查询)
```

AI Agent 拥有三个工具，自主决定调用哪些工具、调用顺序、调用参数。

**方案 B（否决）：三个独立 Agent + 编排器**

```
Orchestrator Agent
  ├── 决策 → SearchAgent | KBRetrievalAgent | HybridAgent
```

**选 A 的理由：**
- 单一 Agent 可以更灵活地组合工具调用（先查 KB，发现不够再搜索 web）
- 减少 Agent 间的上下文传递损失
- 实现更简单，维护成本更低
- LangChain 的 `create_agent()` 原生支持多工具绑定

**否决 B 的理由：**
- 增加不必要的复杂度和延迟
- Agent 间信息传递需要额外的上下文协议
- 编排器的 Prompt 调试成本高

### Decision 2: Agent Prompt 架构

Agent 的 System Prompt 设计为三段式：

1. **角色定义**：告知 Agent 它是一位出题专家
2. **决策引导**：指导 Agent 如何分析 topic 并选择策略
3. **工具使用指南**：说明各工具的适用场景和参数配置

核心决策逻辑（在 Prompt 中引导）：

```
用户输入 topic + subject [+ knowledgeBaseId]
  │
  ├─ 有 KB + topic 适合 KB 检索
  │   → 先调 KnowledgeBaseRetriever
  │   → 结果足够 → 基于 KB 出题 (knowledge_base)
  │   → 结果不足 → 补充 TavilySearch (hybrid)
  │
  ├─ 有 KB + topic 需最新知识
  │   → 先调 TavilySearch
  │   → 再调 KnowledgeBaseRetriever 补充
  │   → 混合出题 (hybrid)
  │
  └─ 无 KB
      → 调 TavilySearch + TavilyExtract (web_search)
      → 基于搜索结果出题
```

### Decision 3: 题目标签系统

| 字段值 | 前端展示标签 | 含义 |
|--------|------------|------|
| `web_search` | 🤖 AI 出题 | 基于联网搜索或模型知识 |
| `model_knowledge` | 🤖 AI 出题 | 基于模型自身知识 |
| `knowledge_base` | 📚 知识库题目 | 基于私有知识库 |

前端 `QuizCard` 根据 `knowledgeSource` 展示对应标签。

### Decision 4: 知识库检索工具封装

将 `RAGQuizChain` 中的 ChromaDB 检索逻辑封装为 LangChain Tool：

```python
class KnowledgeBaseRetriever(BaseTool):
    """从 ChromaDB 知识库检索相关知识块"""
    name = "knowledge_base_retriever"
    description = "从指定知识库中检索与问题相关的知识内容"
    
    kb_id: str
    
    async def _arun(self, query: str, k: int = 5) -> str:
        chunks = await search_similar_chunks(query, kb_id=self.kb_id, k=k)
        # 格式化为文本返回
```

### Decision 5: 前端改造

API 层不变，`searchMode` 参数保留但不再作为路由依据，前端不再发送此参数（或发送空值）。

KnowledgeBaseSelector 组件改造：
- 移除三个搜索模式 chip（仅知识库、仅 AI 搜索、混合模式）
- 用户仍然可以选择知识库（或不选）
- 选择知识库后，AI 自动决定检索策略

QuizCard 组件改造：
- 显示来源标签：`knowledgeSource` → "🤖 AI 出题" 或 "📚 知识库题目"

### Decision 6: 后端路由改造

`quiz_service.py` 中的 `generate_quiz()` 函数：

```python
async def generate_quiz(request: GenerateQuizRequest) -> GenerateQuizResponse:
    # searchMode 参数不再用于路由，保留仅用于向后兼容
    chain = AgenticQuizChain(knowledge_base_id=request.knowledgeBaseId)
    result = await chain.ainvoke(chain_inputs)
    # 每道题根据 knowledgeSource 保留原始值
    # 前端自行映射为展示标签
```

### Decision 7: 与 Tavily search spec 的兼容

当前 `search-augmented-quiz` spec 要求：
- TavilySearch 和 TavilyExtract 作为工具提供给 AI
- AI 自主决定搜索策略（search_depth, max_results, time_range 等）
- 搜索失败时降级

本设计将 KB 检索也作为 Agent 的工具，与 Tavily 工具平级。AI 可以自主决定：
1. 是否搜索（搜索什么、搜索深度）
2. 是否检索 KB（检索什么、检索数量）
3. 搜索和检索的顺序
4. 如何合并结果

## Risks / Trade-offs

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| Agent 决策不稳定（同一 topic 不同次可能选不同策略） | 用户体验不一致 | ① Prompt 中加入确定性引导<br>② 设置 temperature=0.3 降低随机性<br>③ 在 metadata 中记录实际使用的策略供调试 |
| 多工具调用导致响应时间增加 | 用户等待时间变长 | ① 设置单工具调用超时（Tavily 5s, KB 3s）<br>② Agent 整体超时 120s<br>③ 加载动画维持现有分阶段提示 |
| Agent 可能跳过 KB 检索（即使选了 KB） | 用户困惑"选了 KB 为何不用" | ① Prompt 明确要求：如果有 knowledgeBaseId，必须优先检索 KB<br>② 在 metadata 中记录 AI 的决策过程和原因<br>③ 前端展示"AI 正在分析：优先从知识库检索..." |
| DeepSeek Agent 调用多工具稳定性 | 工具调用解析失败 | ① 设置 max_retries=2<br>② 捕获异常后降级为传统搜索增强出题链 |
| KB 检索结果为空时 Agent 反应不当 | 生成空题目 | ① KB 检索结果为空时，Agent 自动切换到 web 搜索<br>② 最终仍无结果则返回明确错误信息 |
