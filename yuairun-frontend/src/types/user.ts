/** 用户系统类型定义 */

/** 用户基本信息 */
export interface UserInfo {
  id: string
  nickname: string
  avatarUrl: string
  xp: number
  level: number
  levelTitle: string
  isNewUser: boolean
}

/** 用户学习统计 */
export interface UserStats {
  totalQuizzes: number
  totalQuestions: number
  totalCorrect: number
  totalWrong: number
  accuracy: number
  totalDuration: number
  streakDays: number
  lastActiveDate: string | null
}

/** 个人中心数据 */
export interface ProfileData {
  id: string
  nickname: string
  avatarUrl: string
  xp: number
  level: number
  levelTitle: string
  nextLevelXp: number
  stats: UserStats
  recentHistories: HistoryItem[]
}

/** 登录响应 */
export interface LoginResponse {
  success: boolean
  data?: {
    token: string
    expiresIn: number
    user: UserInfo
  }
  error?: string
}

/** 个人资料响应 */
export interface ProfileResponse {
  success: boolean
  data?: ProfileData
  error?: string
}

/** 闯关历史列表项 */
export interface HistoryItem {
  id: string
  subject: string
  topic: string
  questionCount: number
  correctCount: number
  accuracy: number
  duration: number
  xpEarned: number
  createdAt: string
}

/** 分页响应 */
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
  hasMore: boolean
}

/** 历史列表响应 */
export interface HistoryListResponse {
  success: boolean
  data?: PaginatedResponse<HistoryItem>
  error?: string
}

/** 错题本列表项 */
export interface WrongBookItem {
  id: string
  question: {
    id: string
    type: string
    question: string
    options: Array<{ label: string; content: string }>
    answer: string | string[]
    explanation: string
    difficulty: string
    knowledgePoint: string
  }
  userAnswer: string
  correctAnswer: string
  subject: string
  topic: string
  wrongCount: number
  lastWrongAt: string
  isMastered: boolean
}

/** 错题本响应 */
export interface WrongBookResponse {
  success: boolean
  data?: PaginatedResponse<WrongBookItem>
  error?: string
}

/** 同步响应 */
export interface SyncResponse {
  success: boolean
  data?: {
    syncedCount: number
    totalCount: number
    xpEarned: number
    currentXp: number
    currentLevel: number
  }
  error?: string
}

/** 通用消息响应 */
export interface MessageResponse {
  success: boolean
  data?: {
    message: string
  }
  error?: string
}
