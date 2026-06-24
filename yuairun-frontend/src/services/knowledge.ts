/** 知识库相关 API */
import Taro from '@tarojs/taro'
import { request } from './request'
import type {
  KnowledgeBaseListResponse,
  KnowledgeDocumentListResponse,
  CreateKnowledgeBaseRequest,
  DocumentUploadResponse,
  DeleteResponse,
} from '../types/knowledge'
import { API_BASE_URL, STORAGE_KEYS } from '../utils/constants'
import { getStorageData } from '../utils/storage'

/** 获取知识库列表 */
export async function getKnowledgeBases(): Promise<KnowledgeBaseListResponse> {
  return request<KnowledgeBaseListResponse>({
    url: '/api/knowledge/bases',
    method: 'GET',
  })
}

/** 创建知识库 */
export async function createKnowledgeBase(
  params: CreateKnowledgeBaseRequest
): Promise<{ success: boolean; error?: string }> {
  return request({
    url: '/api/knowledge/base',
    method: 'POST',
    data: params,
  })
}

/** 删除知识库 */
export async function deleteKnowledgeBase(
  kbId: string
): Promise<DeleteResponse> {
  return request({
    url: `/api/knowledge/base/${kbId}`,
    method: 'DELETE',
  })
}

/** 获取知识库文档列表 */
export async function getKbDocuments(
  kbId: string
): Promise<KnowledgeDocumentListResponse> {
  return request({
    url: `/api/knowledge/base/${kbId}/documents`,
    method: 'GET',
  })
}

/** 上传文档到知识库 */
export async function uploadDocument(
  kbId: string,
  filePath: string
): Promise<DocumentUploadResponse> {
  const token = getStorageData<string | null>(STORAGE_KEYS.TOKEN, null)
  const header: Record<string, string> = {}
  if (token) {
    header['Authorization'] = `Bearer ${token}`
  }

  try {
    const response = await Taro.uploadFile({
      url: `${API_BASE_URL}/api/knowledge/base/${kbId}/documents`,
      filePath,
      name: 'file',
      header,
    })
    return JSON.parse(response.data) as DocumentUploadResponse
  } catch (error) {
    return { success: false, error: '文件上传失败' }
  }
}

/** 删除文档 */
export async function deleteDocument(
  docId: string
): Promise<DeleteResponse> {
  return request({
    url: `/api/knowledge/document/${docId}`,
    method: 'DELETE',
  })
}
