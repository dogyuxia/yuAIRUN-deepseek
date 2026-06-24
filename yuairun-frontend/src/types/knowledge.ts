/** 知识库相关类型定义 */

/** 知识库信息 */
export interface KnowledgeBase {
  id: string
  name: string
  description: string
  isSystem: boolean
  docCount: number
  chunkCount: number
  createdAt: string
  updatedAt: string
}

/** 知识库文档信息 */
export interface KnowledgeDocument {
  id: string
  kbId: string
  filename: string
  fileType: string
  fileSize: number
  pageCount: number | null
  charCount: number
  chunkCount: number
  status: 'pending' | 'processing' | 'ready' | 'failed'
  errorMsg: string | null
  createdAt: string
}

/** 创建知识库请求 */
export interface CreateKnowledgeBaseRequest {
  name: string
  description?: string
}

/** 知识库列表响应 */
export interface KnowledgeBaseListResponse {
  success: boolean
  data: KnowledgeBase[]
  error?: string
}

/** 文档列表响应 */
export interface KnowledgeDocumentListResponse {
  success: boolean
  data: KnowledgeDocument[]
  error?: string
}

/** 上传文档响应 */
export interface DocumentUploadResponse {
  success: boolean
  documentId?: string
  error?: string
}

/** 删除响应 */
export interface DeleteResponse {
  success: boolean
  error?: string
}

/** 搜索模式 */
export type SearchMode = 'search' | 'knowledge_base' | 'hybrid'
