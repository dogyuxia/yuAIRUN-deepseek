/** 答题状态管理 (Zustand) */
import { create } from 'zustand'
import type { QuizQuestion } from '../types/quiz'
import type { QuizRecord } from '../types/quiz'
import { generateId } from '../utils/format'

interface QuizState {
  /** 当前题目列表 */
  questions: QuizQuestion[]
  /** 当前题目索引 */
  currentIndex: number
  /** 用户答案 {questionId: answer} */
  userAnswers: Record<string, string | string[]>
  /** 答题开始时间 */
  startTime: number
  /** 是否正确完成 */
  isFinished: boolean
  /** 是否正在加载 */
  isLoading: boolean
  /** 加载错误 */
  error: string | null

  // 学科/主题信息
  subject: string
  topic: string

  /** 上次完成的答题记录（用于结果页和报告页） */
  lastRecord: QuizRecord | null

  // Actions
  setQuizData: (questions: QuizQuestion[], subject: string, topic: string) => void
  submitAnswer: (questionId: string, answer: string | string[]) => void
  nextQuestion: () => void
  prevQuestion: () => void
  finishQuiz: () => QuizRecord
  resetQuiz: () => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
}

export const useQuizStore = create<QuizState>((set, get) => ({
  questions: [],
  currentIndex: 0,
  userAnswers: {},
  startTime: Date.now(),
  isFinished: false,
  isLoading: false,
  error: null,
  subject: '',
  topic: '',
  lastRecord: null,

  setQuizData: (questions, subject, topic) =>
    set({
      questions,
      subject,
      topic,
      currentIndex: 0,
      userAnswers: {},
      startTime: Date.now(),
      isFinished: false,
      error: null,
    }),

  submitAnswer: (questionId, answer) =>
    set((state) => ({
      userAnswers: { ...state.userAnswers, [questionId]: answer },
    })),

  nextQuestion: () =>
    set((state) => {
      const next = state.currentIndex + 1
      if (next >= state.questions.length) {
        return { isFinished: true }
      }
      return { currentIndex: next }
    }),

  prevQuestion: () =>
    set((state) => ({
      currentIndex: Math.max(0, state.currentIndex - 1),
    })),

  finishQuiz: () => {
    const state = get()
    const correctCount = state.questions.filter((q) => {
      const ua = state.userAnswers[q.id]
      if (!ua) return false
      if (Array.isArray(q.answer)) {
        return Array.isArray(ua) && JSON.stringify([...ua].sort()) === JSON.stringify([...q.answer].sort())
      }
      return String(ua) === String(q.answer)
    }).length

    const record: QuizRecord = {
      id: generateId(),
      subject: state.subject,
      topic: state.topic,
      questions: state.questions,
      userAnswers: state.userAnswers,
      correctCount,
      totalCount: state.questions.length,
      accuracy: state.questions.length > 0 ? correctCount / state.questions.length : 0,
      duration: Math.floor((Date.now() - state.startTime) / 1000),
      createdAt: Date.now(),
      wrongQuestions: state.questions.filter((q) => {
        const ua = state.userAnswers[q.id]
        if (!ua) return true
        if (Array.isArray(q.answer)) {
          return !(Array.isArray(ua) && JSON.stringify([...ua].sort()) === JSON.stringify([...q.answer].sort()))
        }
        return String(ua) !== String(q.answer)
      }),
    }

    set({ lastRecord: record, isFinished: true })
    return record
  },

  resetQuiz: () =>
    set({
      questions: [],
      currentIndex: 0,
      userAnswers: {},
      startTime: Date.now(),
      isFinished: false,
      isLoading: false,
      error: null,
      subject: '',
      topic: '',
    }),

  setLoading: (loading) => set({ isLoading: loading }),

  setError: (error) => set({ error }),
}))
