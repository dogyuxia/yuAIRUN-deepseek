/** 题目相关类型定义 */

/** 题目类型 */
export type QuestionType = 'single' | 'multiple' | 'judge'

/** 难度 */
export type Difficulty = 'easy' | 'medium' | 'hard'

/** 选项 */
export interface QuizOption {
  label: string
  content: string
}

/** 知识来源类型 */
export type KnowledgeSource = 'web_search' | 'model_knowledge' | 'knowledge_base'

/** 知识来源对应的展示标签 */
export const KNOWLEDGE_SOURCE_LABELS: Record<KnowledgeSource, { label: string; icon: string }> = {
  web_search: { label: 'AI 出题', icon: '🤖' },
  model_knowledge: { label: 'AI 出题', icon: '🤖' },
  knowledge_base: { label: '知识库题目', icon: '📚' },
}

/** 根据 knowledgeSource 获取展示标签 */
export function getKnowledgeSourceLabel(source?: KnowledgeSource): string {
  if (!source) return '🤖 AI 出题'
  const info = KNOWLEDGE_SOURCE_LABELS[source]
  return info ? `${info.icon} ${info.label}` : '🤖 AI 出题'
}

/** 单道题目 */
export interface QuizQuestion {
  id: string
  type: QuestionType
  question: string
  options: QuizOption[]
  answer: string | string[]
  explanation: string
  difficulty: Difficulty
  knowledgePoint: string
  /** 知识来源: web_search=基于搜索结果, model_knowledge=基于模型知识, knowledge_base=基于知识库 */
  knowledgeSource?: KnowledgeSource
}

/** 题目元数据 */
export interface QuizMetadata {
  subject: string
  topic: string
  generatedAt: string
  model: string
  /** 是否使用了搜索增强 */
  searchEnhanced?: boolean
  /** 搜索来源 URL 列表 */
  searchSources?: string[]
}

/** AI 生成的题目数据 */
export interface QuizData {
  questions: QuizQuestion[]
  metadata: QuizMetadata
}

/** 用户答题记录 */
export interface QuizRecord {
  id: string
  subject: string
  topic: string
  questions: QuizQuestion[]
  userAnswers: Record<string, string | string[]>
  correctCount: number
  totalCount: number
  accuracy: number
  duration: number
  createdAt: number
  wrongQuestions: QuizQuestion[]
}
