# search-augmented-quiz Specification (Delta)

> Delta spec for the existing `search-augmented-quiz` capability.
> The `TavilySearch` and `TavilyExtract` tools are now sub-tools within the larger `AgenticQuizChain`.
> The `KnowledgeBaseRetriever` tool is added alongside them.
> The "always enabled" requirement is modified to account for the new Agent-based architecture.

## MODIFIED Requirements

### Requirement: Search enhancement is always enabled

The system SHALL always run the AgenticQuizChain for every quiz generation request. The Agent SHALL autonomously decide whether to use Tavily search/extract, KnowledgeBaseRetriever, or both. There SHALL be no user-facing toggle to disable retrieval enhancement. The Agent SHALL always attempt at least one retrieval method.

#### Scenario: Normal quiz generation flow
- **WHEN** user submits a quiz generation request
- **THEN** the system SHALL always invoke the AgenticQuizChain
- **AND** the Agent SHALL always attempt at least one retrieval method (web or KB)
- **AND** users SHALL NOT see any retrieval-strategy-related UI controls

#### Scenario: All retrieval methods fail
- **WHEN** both Tavily search/extract AND KnowledgeBaseRetriever fail or return empty results
- **THEN** the Agent SHALL fall back to generating questions using only model knowledge
- **AND** all questions SHALL have `knowledgeSource: "model_knowledge"`
- **AND** the system SHALL record a warning log

## ADDED Requirements

### Requirement: AI retrieves from knowledge base with KnowledgeBaseRetriever

The system SHALL equip the AI Agent with a `KnowledgeBaseRetriever` tool that queries ChromaDB. The AI SHALL autonomously decide when to call this tool, typically when the user has selected a knowledge base. The AI SHALL dynamically set the query and `k` (number of chunks) based on the user's topic.

#### Scenario: User selected a knowledge base
- **WHEN** the user provides `knowledgeBaseId` in the request
- **THEN** the Agent SHALL have access to the `KnowledgeBaseRetriever` tool configured with that ID
- **AND** the Agent SHALL prioritize KB retrieval when the topic matches KB content

#### Scenario: KB retrieval succeeds
- **WHEN** `KnowledgeBaseRetriever` returns chunks with relevant content
- **THEN** the Agent SHALL use these chunks as primary reference material
- **AND** the Agent MAY supplement with TavilySearch if more diverse content is needed

#### Scenario: KB retrieval returns empty
- **WHEN** `KnowledgeBaseRetriever` returns zero chunks
- **THEN** the Agent SHALL fall back to `TavilySearch` and `TavilyExtract`
- **AND** the system SHALL record a warning log that KB retrieval was empty

### Requirement: AI generates quiz based on all collected materials

The system SHALL provide the Agent with a Prompt that instructs it to: first gather relevant materials using any combination of TavilySearch, TavilyExtract, and KnowledgeBaseRetriever, then generate quiz questions based on those materials. Each question SHALL be labeled with its specific knowledge source.

#### Scenario: Agent-driven quiz generation with any source
- **WHEN** the Agent has collected materials from any combination of tools
- **THEN** the Agent SHALL synthesize the collected materials
- **AND** generate quiz questions based on the materials
- **AND** each question's `knowledgeSource` SHALL accurately reflect its origin

#### Scenario: Knowledge base as primary source
- **WHEN** questions are primarily based on KB content
- **THEN** those questions SHALL have `knowledgeSource: "knowledge_base"`
- **AND** the Agent SHALL prioritize KB-derived questions when KB content is available

#### Scenario: Web search as primary source
- **WHEN** questions are primarily based on Tavily search/extract results
- **THEN** those questions SHALL have `knowledgeSource: "web_search"` or `"model_knowledge"` as appropriate
