# agentic-quiz-strategy Specification

## Purpose
AI 自主判断检索方式的出题策略——AI Agent 分析用户输入，决定联网搜索、知识库检索还是混合检索，动态设置检索参数，最终生成带来源标签的题目。

## Requirements

### Requirement: AI autonomously decides retrieval strategy

The system SHALL provide an AI Agent that autonomously analyzes the user's topic and decides the optimal retrieval strategy. The Agent SHALL have access to three tools: `TavilySearch`, `TavilyExtract`, and `KnowledgeBaseRetriever`. The Agent SHALL dynamically decide which tools to invoke, in what order, and with what parameters.

#### Scenario: User selects a knowledge base
- **WHEN** the user provides a `knowledgeBaseId` (chooses a knowledge base)
- **THEN** the Agent SHALL prioritize the `KnowledgeBaseRetriever` tool for initial information gathering
- **AND** the Agent SHALL evaluate whether KB retrieval results are sufficient
- **AND** if KB results are insufficient (empty or low relevance), the Agent SHALL supplement with `TavilySearch` and `TavilyExtract`
- **AND** the Agent SHALL record in metadata which tools were invoked and why

#### Scenario: User does not select a knowledge base
- **WHEN** the user does not provide a `knowledgeBaseId`
- **THEN** the Agent SHALL use `TavilySearch` and optionally `TavilyExtract` for web-based retrieval
- **AND** the Agent SHALL dynamically set `search_depth` ("basic" or "advanced") based on topic complexity
- **AND** the Agent SHALL dynamically set `max_results` (3-8) based on topic breadth

#### Scenario: Topic involves latest/trending knowledge
- **WHEN** the user's topic is time-sensitive (e.g., "React 19 new features", "2026 AI trends")
- **THEN** the Agent SHALL set `time_range` on TavilySearch (e.g., "year" or "month")
- **AND** the Agent SHALL prioritize `TavilySearch` over `KnowledgeBaseRetriever`

#### Scenario: Topic is well-established knowledge
- **WHEN** the user's topic is a well-established concept (e.g., "TCP三次握手", "线性回归")
- **THEN** the Agent MAY rely more on the `KnowledgeBaseRetriever` if a KB is selected
- **AND** the Agent MAY use `TavilySearch` with `search_depth: "basic"` and fewer results

#### Scenario: Knowledge base retrieval returns no results
- **WHEN** `KnowledgeBaseRetriever` returns zero chunks for the given topic
- **THEN** the Agent SHALL automatically fall back to `TavilySearch` and `TavilyExtract`
- **AND** the Agent SHALL generate quiz questions from web search results
- **AND** the system SHALL record a warning log that KB retrieval was empty

### Requirement: Agent dynamically configures tool parameters

The Agent SHALL dynamically configure tool parameters based on its analysis of the user's query, rather than using fixed defaults. This includes search depth, result count, time range, and KB chunk count.

#### Scenario: Complex topic requires deep search
- **WHEN** the Agent determines the topic is complex or requires specialized knowledge
- **THEN** the Agent SHALL set `search_depth: "advanced"` on TavilySearch
- **AND** the Agent MAY increase `max_results` to 8 for broader coverage

#### Scenario: Simple topic requires basic search
- **WHEN** the Agent determines the topic is straightforward or foundational
- **THEN** the Agent SHALL use `search_depth: "basic"` on TavilySearch
- **AND** the Agent MAY set `max_results` to 3-5 for focused results

#### Scenario: KB retrieval for narrow topics
- **WHEN** the Agent calls `KnowledgeBaseRetriever` for a specific/narrow query
- **THEN** the Agent SHALL set `k` (number of chunks) between 3-5
- **AND** the Agent MAY use a broader query for KB search if the topic is not found

### Requirement: Questions are tagged with knowledge source

Each generated question SHALL include a `knowledgeSource` field that indicates the origin of the question's content. The frontend SHALL display a human-readable tag based on this field.

#### Scenario: Question based on web search
- **WHEN** a question's content is derived from Tavily search/extract results
- **THEN** the question SHALL have `knowledgeSource: "web_search"`
- **AND** the frontend SHALL display the tag "🤖 AI 出题"

#### Scenario: Question based on model knowledge
- **WHEN** a question's content is derived from the AI model's own knowledge (no search results or supplementing)
- **THEN** the question SHALL have `knowledgeSource: "model_knowledge"`
- **AND** the frontend SHALL display the tag "🤖 AI 出题"

#### Scenario: Question based on knowledge base
- **WHEN** a question's content is derived from knowledge base retrieval (ChromaDB)
- **THEN** the question SHALL have `knowledgeSource: "knowledge_base"`
- **AND** the frontend SHALL display the tag "📚 知识库题目"

#### Scenario: Mixed sources in same quiz
- **WHEN** a quiz set contains questions from multiple sources (e.g., both KB and web)
- **THEN** each question SHALL independently have its own `knowledgeSource` value
- **AND** different questions in the same quiz MAY have different source tags

### Requirement: Response metadata includes decision trace

The API response SHALL include metadata that records the Agent's decision-making process, enabling debugging and user transparency.

#### Scenario: Successful agentic generation
- **WHEN** the Agent successfully generates quiz questions
- **THEN** the response metadata SHALL include `searchMode: "agentic"`
- **AND** SHALL include `retrievalStrategy` field describing which tools were used (e.g., "kb_only", "web_only", "kb_then_web", "web_then_kb")
- **AND** SHALL include `toolsInvoked` array listing the tool names that were called
- **AND** SHALL include `searchSources` array with URLs of accessed web pages

#### Scenario: Agent fails to decide
- **WHEN** the Agent encounters an error during tool invocation or decision-making
- **THEN** the system SHALL fall back to the existing `SearchAugmentedQuizChain`
- **AND** the response metadata SHALL include `fallback: true`
- **AND** the system SHALL record an error log with the failure reason

### Requirement: UI hides strategy complexity from user

The frontend SHALL abstract away the retrieval strategy selection. Users SHALL NOT see search mode options or strategy controls. The only user-facing choice is whether to select a knowledge base.

#### Scenario: Topic input page without strategy selector
- **WHEN** the user is on the topic input page
- **THEN** the UI SHALL NOT display search mode options (search/knowledge_base/hybrid chips)
- **AND** the UI SHALL display knowledge base selector as an optional configuration
- **AND** the UI SHALL display the current knowledge base name (if selected) as a simple tag

#### Scenario: Quiz card shows source tag
- **WHEN** the user is on the quiz page viewing a question
- **THEN** each question card SHALL display a source tag based on `knowledgeSource`
- **AND** the source tag SHALL be: "🤖 AI 出题" or "📚 知识库题目"
- **AND** the source tag SHALL be visually subtle but readable (small, muted color)

### Requirement: Backward compatibility with existing API

The system SHALL maintain backward compatibility with the existing `/api/quiz/generate` API. The `searchMode` parameter SHALL be accepted but ignored (the Agent always decides). The `knowledgeBaseId` parameter SHALL continue to work as before.

#### Scenario: Request with searchMode parameter
- **WHEN** a client sends a request with `searchMode` set to any value
- **THEN** the system SHALL ignore the `searchMode` value
- **AND** the Agent SHALL autonomously decide the strategy regardless

#### Scenario: Request without searchMode parameter
- **WHEN** a client sends a request without `searchMode`
- **THEN** the system SHALL treat it as `searchMode: "agentic"` (default)
- **AND** the Agent SHALL autonomously decide the strategy

#### Scenario: Request with knowledgeBaseId
- **WHEN** a client sends a request with `knowledgeBaseId`
- **THEN** the Agent SHALL use the `KnowledgeBaseRetriever` tool with that ID
- **AND** the Agent SHALL prioritize KB retrieval as per its decision logic
