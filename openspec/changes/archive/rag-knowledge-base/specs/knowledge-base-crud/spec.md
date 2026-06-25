## ADDED Requirements

### Requirement: User can create a knowledge base

The system SHALL allow authenticated users to create a knowledge base. A knowledge base is a named container for documents that can be used for RAG-based quiz generation. System knowledge bases SHALL be automatically created and visible to all users.

#### Scenario: User creates a new knowledge base
- **WHEN** user sends POST to `/api/knowledge/base` with `name` and optional `description`
- **THEN** the system SHALL create a new knowledge base record in MySQL
- **AND** return the knowledge base ID, name, description, and creation time
- **AND** the knowledge base SHALL be empty (0 documents)

#### Scenario: User creates knowledge base with duplicate name
- **WHEN** user sends POST to `/api/knowledge/base` with a `name` that already exists for this user
- **THEN** the system SHALL allow creation (different users may have same name)
- **AND** SHALL return the new knowledge base with a unique ID

#### Scenario: System knowledge bases exist
- **WHEN** the application starts up
- **THEN** the system SHALL seed built-in knowledge bases (e.g., "AI Agent 知识库")
- **AND** these knowledge bases SHALL have `is_system = true` and `user_id = 'system'`

### Requirement: User can list their knowledge bases

The system SHALL allow authenticated users to retrieve a list of their own knowledge bases, including system knowledge bases.

#### Scenario: List knowledge bases
- **WHEN** user sends GET to `/api/knowledge/bases`
- **THEN** the system SHALL return all knowledge bases belonging to this user
- **AND** SHALL include system knowledge bases (`is_system = true`)
- **AND** SHALL include `docCount` and `chunkCount` for each knowledge base
- **AND** results SHALL be sorted by `updatedAt` descending

#### Scenario: Empty knowledge base list
- **WHEN** a new user who has not created any knowledge base sends GET to `/api/knowledge/bases`
- **THEN** the system SHALL return at least the system knowledge bases
- **AND** SHALL NOT return an error

### Requirement: User can delete a knowledge base

The system SHALL allow authenticated users to delete their own knowledge bases. System knowledge bases SHALL NOT be deletable by regular users.

#### Scenario: User deletes their own knowledge base
- **WHEN** user sends DELETE to `/api/knowledge/base/{id}` for a knowledge base they own
- **THEN** the system SHALL delete the knowledge base record from MySQL
- **AND** SHALL delete all document records associated with this knowledge base
- **AND** SHALL delete corresponding vectors from ChromaDB
- **AND** SHALL delete uploaded files from disk

#### Scenario: User tries to delete a system knowledge base
- **WHEN** user sends DELETE to `/api/knowledge/base/{id}` for a system knowledge base
- **THEN** the system SHALL return `{ "success": false, "error": "不能删除系统知识库" }`

#### Scenario: User tries to delete another user's knowledge base
- **WHEN** user sends DELETE to `/api/knowledge/base/{id}` for a knowledge base owned by another user
- **THEN** the system SHALL return a 404 or permission error

### Requirement: Knowledge base has usage limits

The system SHALL enforce reasonable limits on knowledge base creation and storage to prevent abuse.

#### Scenario: User exceeds knowledge base limit
- **WHEN** user has reached the maximum number of knowledge bases (10)
- **THEN** the system SHALL return `{ "success": false, "error": "知识库数量已达上限（10个）" }`

#### Scenario: User exceeds document count per knowledge base
- **WHEN** a knowledge base has reached the maximum document count (50)
- **THEN** the system SHALL reject further document uploads with a clear error message
