/** 用户状态管理 (Zustand) */
import { create } from 'zustand'
import { getStorageData, setStorageData } from '../utils/storage'
import { STORAGE_KEYS } from '../utils/constants'
import type { QuizRecord } from '../types/quiz'

interface UserState {
  /** 答题历史 */
  history: QuizRecord[]
  /** 经验值 */
  xp: number
  /** 最近输入的学科 */
  lastSubject: string

  // Actions
  addHistory: (record: QuizRecord) => void
  addXp: (amount: number) => void
  setLastSubject: (subject: string) => void
  loadFromStorage: () => void
}

export const useUserStore = create<UserState>((set, get) => ({
  history: [],
  xp: 0,
  lastSubject: '',

  addHistory: (record) =>
    set((state) => {
      const newHistory = [record, ...state.history].slice(0, 50)
      setStorageData(STORAGE_KEYS.QUIZ_HISTORY, newHistory)
      return { history: newHistory }
    }),

  addXp: (amount) =>
    set((state) => {
      const newXp = state.xp + amount
      setStorageData(STORAGE_KEYS.USER_XP, newXp)
      return { xp: newXp }
    }),

  setLastSubject: (subject) => set({ lastSubject: subject }),

  loadFromStorage: () => {
    const history = getStorageData<QuizRecord[]>(STORAGE_KEYS.QUIZ_HISTORY, [])
    const xp = getStorageData<number>(STORAGE_KEYS.USER_XP, 0)
    set({ history, xp })
  },
}))
