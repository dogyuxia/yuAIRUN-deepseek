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
}

/** 题目元数据 */
export interface QuizMetadata {
  subject: string
  topic: string
  generatedAt: string
  model: string
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
