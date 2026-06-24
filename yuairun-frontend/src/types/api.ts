/** API 响应类型定义 */
import type { QuizData, QuizQuestion } from './quiz'
import type { AnalyzeReportData } from './report'

/** 生成题目请求 */
export interface GenerateQuizRequest {
  subject: string
  topic: string
  count: number
  difficulty: string
  type: string
  /** 🆕 知识库 ID（指定后从该知识库检索） */
  knowledgeBaseId?: string
  /** 🆕 搜索模式 */
  searchMode?: 'search' | 'knowledge_base' | 'hybrid'
}

/** 生成题目响应 */
export interface GenerateQuizResponse {
  success: boolean
  data?: QuizData
  error?: string
  detail?: string
}

/** 分析报告请求 */
export interface AnalyzeQuizRequest {
  subject: string
  topic: string
  questions: QuizQuestion[]
  userAnswers: Record<string, string | string[]>
  duration: number
}

/** 分析报告响应 */
export interface AnalyzeQuizResponse {
  success: boolean
  data?: AnalyzeReportData
  error?: string
}
