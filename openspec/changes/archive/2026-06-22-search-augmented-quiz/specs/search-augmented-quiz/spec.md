## ADDED Requirements

### Requirement: AI autonomously searches with TavilySearch

The system SHALL equip the AI with the `TavilySearch` tool from `langchain-tavily`. The AI SHALL autonomously decide when to call this tool based on the user's input. The AI SHALL dynamically set tool parameters including `search_depth` (basic/advanced), `max_results`, `time_range`, `include_domains`, and `exclude_domains` based on the complexity and nature of the query.

#### Scenario: User inputs a keyword/topic
- **WHEN** the user inputs a textual topic (e.g., "Harness Engineering", "量子计算最新进展")
- **THEN** the AI SHALL call `TavilySearch` with a query combining the topic and subject
- **AND** the AI SHALL dynamically choose `search_depth` ("basic" for simple concepts, "advanced" for complex/new knowledge)
- **AND** the AI SHALL dynamically set `max_results` (e.g., 3 for narrow topics, 8 for broad topics)
- **AND** the AI SHALL set `time_range` when the topic is time-sensitive (e.g., "year" for trending topics)
- **AND** the AI SHALL consider `include_domains`/`exclude_domains` for quality control

#### Scenario: Search returns relevant results
- **WHEN** TavilySearch returns results with title, URL, content snippet, and optional raw_content
- **THEN** the AI SHALL use these results as reference materials for quiz generation
- **AND** the AI SHALL evaluate result quality and supplement with its own knowledge if needed

#### Scenario: Search returns no results
- **WHEN** TavilySearch returns 0 results
- **THEN** the AI SHALL fall back to its own knowledge for quiz generation
- **AND** the system SHALL record a warning log

### Requirement: AI extracts full page content with TavilyExtract

The system SHALL equip the AI with the `TavilyExtract` tool from `langchain-tavily`. The AI SHALL autonomously decide when to call this tool, typically when the user input is a URL or when a search result needs deeper content analysis.

#### Scenario: User inputs a URL
- **WHEN** the user inputs a URL (e.g., a blog post, paper, documentation page)
- **THEN** the AI SHALL call `TavilyExtract` with `urls` containing the user's URL
- **AND** the AI SHALL dynamically set `extract_depth` ("basic" for simple pages, "advanced" for in-depth content)

#### Scenario: AI decides to extract from a search result
- **WHEN** the AI finds a promising search result that requires full content for accurate quiz generation
- **THEN** the AI SHALL call `TavilyExtract` with that result's URL for deeper content extraction

#### Scenario: URL extraction fails
- **WHEN** TavilyExtract returns `failed_results` or empty `results`
- **THEN** the AI SHALL fall back to using search snippets or its own knowledge
- **AND** the system SHALL record a warning log

### Requirement: AI generates quiz based on collected materials

The system SHALL provide the AI with a Prompt that instructs it to: first gather relevant materials using TavilySearch and TavilyExtract, then generate quiz questions based on those materials. Each question SHALL be labeled with its knowledge source.

#### Scenario: Agent-driven quiz generation
- **WHEN** the AI has collected search/extract results
- **THEN** the AI SHALL synthesize the collected materials
- **AND** generate quiz questions based on the materials
- **AND** each question's `knowledgeSource` field SHALL indicate "web_search" or "model_knowledge"

#### Scenario: Mixed knowledge sources
- **WHEN** the AI combines web search results with its own knowledge
- **THEN** questions based on search results SHALL have `knowledgeSource: "web_search"`
- **AND** questions based on model knowledge SHALL have `knowledgeSource: "model_knowledge"`

### Requirement: Response includes search enhancement metadata

The API response for quiz generation SHALL include metadata about whether search enhancement was used and which sources were referenced.

#### Scenario: Search-enhanced response
- **WHEN** Tavily tools were successfully used
- **THEN** the response metadata SHALL include `searchEnhanced: true`
- **AND** SHALL include `searchSources` array listing the URLs of successfully accessed pages
- **AND** each question SHALL include `knowledgeSource` field

#### Scenario: Degraded response (search failed)
- **WHEN** Tavily tools failed or timed out
- **THEN** the response metadata SHALL include `searchEnhanced: false`
- **AND** `searchSources` SHALL be empty
- **AND** all questions SHALL have `knowledgeSource: "model_knowledge"`
- **AND** the system SHALL record a warning log

### Requirement: Search enhancement is always enabled

The system SHALL always attempt search enhancement for every quiz generation request. There SHALL be no user-facing toggle or switch to disable it. Users do not need to be aware of the search process.

#### Scenario: Normal quiz generation flow
- **WHEN** user submits a quiz generation request
- **THEN** the system SHALL always attempt Tavily search/extract
- **AND** the system SHALL always attempt to enhance the quiz with external knowledge
- **AND** users SHALL NOT see any search-related UI controls
