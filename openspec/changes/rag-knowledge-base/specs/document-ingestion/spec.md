## ADDED Requirements

### Requirement: User can upload documents to a knowledge base

The system SHALL allow authenticated users to upload documents (PDF, DOCX, TXT, Markdown) to an existing knowledge base. Uploaded files SHALL be parsed and indexed for RAG retrieval.

#### Scenario: User uploads a PDF document
- **WHEN** user sends POST to `/api/knowledge/base/{id}/documents` with a PDF file (multipart/form-data)
- **THEN** the system SHALL accept the file and return `{ "success": true, "documentId": "kd_xxx" }`
- **AND** the document status SHALL be `pending`
- **AND** the system SHALL start background processing of the document

#### Scenario: User uploads a DOCX document
- **WHEN** user sends POST to `/api/knowledge/base/{id}/documents` with a DOCX file
- **THEN** the system SHALL accept and process it the same way as PDF
- **AND** the system SHALL extract text content using Docling

#### Scenario: User uploads unsupported file type
- **WHEN** user sends POST with a file type other than PDF, DOCX, TXT, or Markdown
- **THEN** the system SHALL return `{ "success": false, "error": "不支持的文件格式，仅支持 PDF、DOCX、TXT、Markdown" }`

#### Scenario: User uploads file exceeding size limit
- **WHEN** user sends a file larger than 20MB
- **THEN** the system SHALL return `{ "success": false, "error": "文件大小不能超过 20MB" }`

### Requirement: System processes uploaded documents asynchronously

The system SHALL parse uploaded documents, split them into chunks, generate embeddings, and index them in ChromaDB asynchronously.

#### Scenario: Document processing succeeds
- **WHEN** a document is uploaded
- **THEN** the system SHALL process it asynchronously using FastAPI BackgroundTasks
- **AND** SHALL use Docling to parse the document (extract text, tables)
- **AND** SHALL use HybridChunker to split text into semantic chunks
- **AND** SHALL generate embeddings for each chunk using BGE-M3 model
- **AND** SHALL store the vectors in ChromaDB with metadata
- **AND** SHALL update the document status to `ready`
- **AND** SHALL update the document's `chunkCount` in MySQL

#### Scenario: Document processing fails
- **WHEN** document parsing or embedding fails (e.g., corrupted file, unreadable PDF)
- **THEN** the system SHALL set document status to `failed`
- **AND** SHALL record the error message in `errorMsg` field
- **AND** SHALL NOT block other documents in the same knowledge base
- **AND** the user SHALL be able to see the error status in the document list

#### Scenario: User checks document processing status
- **WHEN** user sends GET to `/api/knowledge/base/{id}/documents`
- **THEN** the system SHALL return a list of documents with their current `status`
- **AND** the status SHALL be one of: `pending`, `processing`, `ready`, `failed`

### Requirement: User can delete a document from knowledge base

The system SHALL allow authenticated users to delete documents from their own knowledge bases, which SHALL also remove the associated vectors from ChromaDB.

#### Scenario: User deletes a document
- **WHEN** user sends DELETE to `/api/knowledge/document/{id}`
- **THEN** the system SHALL delete the document record from MySQL
- **AND** SHALL delete corresponding chunks from ChromaDB
- **AND** SHALL delete the uploaded file from disk
- **AND** SHALL update the knowledge base's `docCount` and `chunkCount`

### Requirement: System provides built-in knowledge packages

The system SHALL ship with pre-built knowledge packages that are seeded on first startup. These packages cover the "AI Agent" domain and SHALL be available to all users as read-only knowledge bases.

#### Scenario: System knowledge base is seeded on startup
- **WHEN** the application starts for the first time with an empty database
- **THEN** the system SHALL create a system knowledge base named "AI Agent 知识库"
- **AND** SHALL load pre-built Markdown documents from `backend/knowledge_base/default/`
- **AND** SHALL process and index those documents just like user-uploaded files
- **AND** SHALL set `isSystem = true` for the knowledge base

#### Scenario: System knowledge base already exists
- **WHEN** the application starts and system knowledge bases already exist in MySQL
- **THEN** the system SHALL skip the seeding process
- **AND** SHALL NOT duplicate existing system knowledge bases

### Requirement: User can reindex a knowledge base

The system SHALL allow users to trigger re-indexing of a knowledge base, which re-processes all documents.

#### Scenario: User triggers reindex
- **WHEN** user sends POST to `/api/knowledge/base/{id}/reindex`
- **THEN** the system SHALL delete all existing ChromaDB vectors for this knowledge base
- **AND** SHALL re-process all documents from scratch
- **AND** SHALL update `chunkCount` for each document and the knowledge base
