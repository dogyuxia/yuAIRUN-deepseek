/** 常量定义 */

/** 后端 API 基础地址 */
export const API_BASE_URL = 'http://127.0.0.1:8000'

/** 题目数量选项 */
export const QUIZ_COUNT_OPTIONS = [5, 10, 15, 20] as const

/** 难度选项 */
export const DIFFICULTY_OPTIONS = [
  { label: '简单', value: 'easy' },
  { label: '中等', value: 'medium' },
  { label: '困难', value: 'hard' },
  { label: '混合', value: 'mixed' },
] as const

/** 学科快捷选项 */
export const SUBJECT_QUICK_OPTIONS = [
  { label: '计算机', icon: '📖' },
  { label: '自然科学', icon: '🔬' },
  { label: '语言学习', icon: '📝' },
] as const

/** 本地存储 Key */
export const STORAGE_KEYS = {
  QUIZ_HISTORY: 'yuairun_quiz_history',
  WRONG_BOOK: 'yuairun_wrong_book',
  USER_SETTINGS: 'yuairun_user_settings',
  USER_XP: 'yuairun_user_xp',
} as const

/** 最大存储数量 */
export const MAX_HISTORY_COUNT = 50
export const MAX_WRONG_COUNT = 100
