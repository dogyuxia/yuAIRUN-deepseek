## ADDED Requirements

### Requirement: User can generate quiz from knowledge base

The system SHALL extend the existing quiz generation endpoint to support RAG-based quiz generation from a specified knowledge base. The system SHALL retrieve relevant chunks from ChromaDB and inject them into the LLM prompt as context.

#### Scenario: User generates quiz from a knowledge base
- **WHEN** user sends POST to `/api/quiz/generate` with `knowledgeBaseId: "kb_001"` and `searchMode: "knowledge_base"`
- **THEN** the system SHALL use the knowledge base ID to query ChromaDB for relevant chunks
- **AND** SHALL perform similarity search with the user's `topic` as the query
- **AND** SHALL retrieve the top 5-10 most relevant chunks
- **AND** SHALL format the retrieved chunks as context "参考资料"
- **AND** SHALL inject the context into the RAG prompt
- **AND** SHALL call DeepSeek to generate questions based on the context
- **AND** return the generated questions with `knowledgeSource: "knowledge_base"`

#### Scenario: Knowledge base is empty
- **WHEN** user sends a quiz generation request with a `knowledgeBaseId` that has 0 documents or 0 chunks
- **THEN** the system SHALL return `{ "success": false, "error": "知识库为空，请先上传文档" }`

#### Scenario: Knowledge base not found
- **WHEN** user sends a quiz generation request with a non-existent `knowledgeBaseId`
- **THEN** the system SHALL return `{ "success": false, "error": "知识库不存在" }`

#### Scenario: Knowledge base has insufficient content
- **WHEN** similarity search returns fewer than 2 relevant chunks
- **THEN** the system SHALL return `{ "success": false, "error": "知识库中没有足够的相关内容，请尝试其他知识库或使用搜索模式" }`

### Requirement: System supports multiple search modes for quiz generation

The system SHALL support three search modes for quiz generation: `search` (existing Tavily), `knowledge_base` (new RAG), and `hybrid` (combined).

#### Scenario: User uses search mode (existing behavior)
- **WHEN** user sends POST to `/api/quiz/generate` with `searchMode: "search"` (or omits the field)
- **THEN** the system SHALL use the existing Tavily search-augmented quiz chain
- **AND** behavior SHALL be identical to the current implementation

#### Scenario: User uses hybrid mode (knowledge base + search)
- **WHEN** user sends POST to `/api/quiz/generate` with `searchMode: "hybrid"` and a `knowledgeBaseId`
- **THEN** the system SHALL perform both ChromaDB similarity search AND Tavily web search
- **AND** SHALL merge the results into a unified context
- **AND** SHALL deduplicate overlapping information
- **AND** SHALL inject the merged context into the prompt
- **AND** each question's `knowledgeSource` SHALL indicate `"knowledge_base"` or `"web_search"` or `"hybrid"`

### Requirement: Quiz response includes knowledge base metadata

The system SHALL include knowledge base information in the quiz generation response metadata to indicate which knowledge base was used.

#### Scenario: Knowledge base mode response
- **WHEN** quiz is generated using `searchMode: "knowledge_base"`
- **THEN** the response metadata SHALL include:
  - `searchEnhanced: true`
  - `searchMode: "knowledge_base"`
  - `knowledgeBaseId: "kb_001"`
  - `knowledgeBaseName: "AI Agent 知识库"`
  - `searchSources: ["知识库: 文档名.pdf - 第3块"]`

#### Scenario: Hybrid mode response
- **WHEN** quiz is generated using `searchMode: "hybrid"`
- **THEN** the response metadata SHALL include both search sources and knowledge base sources
- **AND** each question's `knowledgeSource` SHALL indicate the actual source used

### Requirement: RAG quiz prompt differs from search quiz prompt

The system SHALL use a dedicated RAG prompt template that instructs the LLM to prioritize knowledge base content over its own knowledge.

#### Scenario: RAG prompt instructs knowledge base priority
- **WHEN** the system generates quiz using `searchMode: "knowledge_base"`
- **THEN** the prompt SHALL explicitly instruct: "你必须严格基于以下知识库资料出题"
- **AND** the prompt SHALL include the knowledge base name and document list as context
- **AND** questions SHALL be tagged with `knowledgeSource: "knowledge_base"`

### Requirement: User can select knowledge base in the quiz generation UI

The frontend SHALL provide a knowledge base selector in the quiz generation page, allowing users to choose which knowledge base to use or to use the default search mode.

#### Scenario: User sees knowledge base selector
- **WHEN** user opens the topic-input page
- **THEN** the page SHALL show an optional "知识库" section below the topic input
- **AND** SHALL display a list of the user's knowledge bases (including system ones)
- **AND** SHALL show doc count and status for each knowledge base
- **AND** SHALL default to "AI 搜索出题" mode (no knowledge base selected)

#### Scenario: User selects a knowledge base
- **WHEN** user selects a knowledge base from the selector
- **THEN** the selected knowledge base ID SHALL be sent with the quiz generation request
- **AND** the UI SHALL show which knowledge base is being used
- **AND** the UI SHALL indicate whether search mode is "仅知识库" or "混合模式"

#### Scenario: Knowledge base selector shows empty state
- **WHEN** user has no documents in any knowledge base
- **THEN** the selector SHALL still show the system knowledge base (AI Agent 知识库)
- **AND** SHALL show a hint encouraging document upload
