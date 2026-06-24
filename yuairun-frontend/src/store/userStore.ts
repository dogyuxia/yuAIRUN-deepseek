/** 用户状态管理 (Zustand) - 包含本地 + 云端同步 */
import { create } from 'zustand'
import Taro from '@tarojs/taro'
import { getStorageData, setStorageData, removeStorageData } from '../utils/storage'
import { STORAGE_KEYS, LEVEL_THRESHOLDS, LEVEL_TITLES } from '../utils/constants'
import type { QuizRecord } from '../types/quiz'
import type { UserInfo, ProfileData } from '../types/user'
import * as userApi from '../services/user'

interface UserState {
  /** 答题历史 */
  history: QuizRecord[]
  /** 经验值 */
  xp: number
  /** 最近输入的学科 */
  lastSubject: string

  // 用户认证
  token: string | null
  userInfo: UserInfo | null
  isLoggedIn: boolean
  isLoginLoading: boolean
  profile: ProfileData | null

  // Actions - 本地
  addHistory: (record: QuizRecord) => void
  addXp: (amount: number) => void
  setLastSubject: (subject: string) => void
  loadFromStorage: () => void
  getLevel: (xp: number) => number
  getLevelTitle: (level: number) => string
  getNextLevelXp: (xp: number) => number

  // Actions - 用户认证
  silentLogin: () => Promise<void>
  login: (code: string, nickname?: string, avatarUrl?: string) => Promise<boolean>
  manualLogin: (username: string, password: string) => Promise<boolean>
  logout: () => void
  loadUserProfile: () => Promise<void>

  // Actions - 云端同步
  syncHistory: () => Promise<void>
  syncWrongBook: () => Promise<void>
}

export const useUserStore = create<UserState>((set, get) => ({
  history: [],
  xp: 0,
  lastSubject: '',

  token: null,
  userInfo: null,
  isLoggedIn: false,
  isLoginLoading: false,
  profile: null,

  // ============================================================
  // 本地操作
  // ============================================================

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
    const token = getStorageData<string | null>(STORAGE_KEYS.TOKEN, null)
    const userInfo = getStorageData<UserInfo | null>(STORAGE_KEYS.USER_INFO, null)
    set({
      history,
      xp,
      token,
      userInfo,
      isLoggedIn: !!token,
    })
  },

  getLevel: (xp: number) => {
    for (let i = 0; i < LEVEL_THRESHOLDS.length; i++) {
      if (xp < LEVEL_THRESHOLDS[i]) return i
    }
    return LEVEL_THRESHOLDS.length
  },

  getLevelTitle: (level: number) => {
    return level < LEVEL_TITLES.length ? LEVEL_TITLES[level] : '传奇'
  },

  getNextLevelXp: (xp: number) => {
    const level = get().getLevel(xp)
    return level < LEVEL_THRESHOLDS.length ? LEVEL_THRESHOLDS[level] : LEVEL_THRESHOLDS[LEVEL_THRESHOLDS.length - 1] + 1000
  },

  // ============================================================
  // 用户认证
  // ============================================================

  silentLogin: async () => {
    const state = get()
    set({ isLoginLoading: true })

    try {
      // 先尝试用缓存的 Token
      const token = getStorageData<string | null>(STORAGE_KEYS.TOKEN, null)
      const userInfo = getStorageData<UserInfo | null>(STORAGE_KEYS.USER_INFO, null)

      if (token && userInfo) {
        set({ token, userInfo, isLoggedIn: true, xp: userInfo.xp, isLoginLoading: false })
        // 异步加载 profile
        get().loadUserProfile().catch(() => {})
        return
      }

      // 生成稳定的设备 ID（确保每次编译后同一用户）
      let deviceId = getStorageData<string | null>(STORAGE_KEYS.DEVICE_ID, null)
      if (!deviceId) {
        deviceId = `device_${Date.now()}_${Math.random().toString(36).substring(2, 10)}`
        setStorageData(STORAGE_KEYS.DEVICE_ID, deviceId)
      }

      // 调用后端登录（使用稳定的 deviceId 作为 code）
      const res = await userApi.login(deviceId)
      if (res.success && res.data) {
        setStorageData(STORAGE_KEYS.TOKEN, res.data.token)
        setStorageData(STORAGE_KEYS.USER_INFO, res.data.user)
        setStorageData(STORAGE_KEYS.USER_XP, res.data.user.xp)
        // 切用户时清除旧用户的本地历史
        removeStorageData(STORAGE_KEYS.QUIZ_HISTORY)
        set({
          token: res.data.token,
          userInfo: res.data.user,
          isLoggedIn: true,
          xp: res.data.user.xp,
          isLoginLoading: false,
          history: [],
        })
        // 异步加载 profile（含该用户的服务端统计数据）
        get().loadUserProfile().catch(() => {})
      } else {
        set({ isLoginLoading: false })
      }
    } catch (e) {
      console.error('静默登录失败:', e)
      set({ isLoginLoading: false })
    }
  },

  manualLogin: async (username: string, password: string) => {
    try {
      const res = await userApi.manualLogin(username, password)
      if (res.success && res.data) {
        setStorageData(STORAGE_KEYS.TOKEN, res.data.token)
        setStorageData(STORAGE_KEYS.USER_INFO, res.data.user)
        setStorageData(STORAGE_KEYS.USER_XP, res.data.user.xp)
        removeStorageData(STORAGE_KEYS.QUIZ_HISTORY)
        set({
          token: res.data.token,
          userInfo: res.data.user,
          isLoggedIn: true,
          xp: res.data.user.xp,
          history: [],
        })
        return true
      }
      return false
    } catch (e) {
      console.error('手动登录失败:', e)
      return false
    }
  },

  login: async (code, nickname, avatarUrl) => {
    try {
      // 如未提供 code，使用稳定的 deviceId
      let loginCode = code
      if (!loginCode) {
        let deviceId = getStorageData<string | null>(STORAGE_KEYS.DEVICE_ID, null)
        if (!deviceId) {
          deviceId = `device_${Date.now()}_${Math.random().toString(36).substring(2, 10)}`
          setStorageData(STORAGE_KEYS.DEVICE_ID, deviceId)
        }
        loginCode = deviceId
      }

      const res = await userApi.login(loginCode, nickname, avatarUrl)
      if (res.success && res.data) {
        setStorageData(STORAGE_KEYS.TOKEN, res.data.token)
        setStorageData(STORAGE_KEYS.USER_INFO, res.data.user)
        setStorageData(STORAGE_KEYS.USER_XP, res.data.user.xp)
        removeStorageData(STORAGE_KEYS.QUIZ_HISTORY)
        set({
          token: res.data.token,
          userInfo: res.data.user,
          isLoggedIn: true,
          xp: res.data.user.xp,
          history: [],
        })
        return true
      }
      return false
    } catch (e) {
      console.error('登录失败:', e)
      return false
    }
  },

  logout: () => {
    removeStorageData(STORAGE_KEYS.TOKEN)
    removeStorageData(STORAGE_KEYS.USER_INFO)
    removeStorageData(STORAGE_KEYS.DEVICE_ID)
    removeStorageData(STORAGE_KEYS.QUIZ_HISTORY)
    removeStorageData(STORAGE_KEYS.USER_XP)
    set({
      token: null,
      userInfo: null,
      isLoggedIn: false,
      profile: null,
      xp: 0,
      history: [],
    })
  },

  loadUserProfile: async () => {
    try {
      const res = await userApi.getProfile()
      if (res.success && res.data) {
        set({
          profile: res.data,
          xp: res.data.xp,
          userInfo: {
            id: res.data.id,
            nickname: res.data.nickname,
            avatarUrl: res.data.avatarUrl,
            xp: res.data.xp,
            level: res.data.level,
            levelTitle: res.data.levelTitle,
            isNewUser: false,
          },
        })
        // 同步更新存储中的 userInfo 和 XP
        setStorageData(STORAGE_KEYS.USER_INFO, {
          id: res.data.id,
          nickname: res.data.nickname,
          avatarUrl: res.data.avatarUrl,
          xp: res.data.xp,
          level: res.data.level,
          levelTitle: res.data.levelTitle,
          isNewUser: false,
        })
        setStorageData(STORAGE_KEYS.USER_XP, res.data.xp)
      }
    } catch (e) {
      // 加载失败（如 token 过期）时保留缓存数据，不清除登录状态
      console.warn('加载用户信息失败（保留缓存）:', e)
    }
  },

  // ============================================================
  // 云端同步
  // ============================================================

  syncHistory: async () => {
    const { token, history } = get()
    if (!token || history.length === 0) return

    try {
      // 只同步上次同步之后新增的记录
      const lastSyncTime = getStorageData<number>(STORAGE_KEYS.LAST_SYNC_TIME, 0)
      const newRecords = history.filter((h) => h.createdAt > lastSyncTime)
      if (newRecords.length === 0) return

      const records = newRecords.map((h) => ({
        subject: h.subject,
        topic: h.topic,
        questions: h.questions,
        userAnswers: h.userAnswers,
        correctCount: h.correctCount,
        totalCount: h.totalCount,
        accuracy: h.accuracy,
        duration: h.duration,
        createdAt: new Date(h.createdAt).toISOString(),
      }))

      const res = await userApi.syncHistory(records)
      if (res.success && res.data) {
        // 更新同步时间戳
        setStorageData(STORAGE_KEYS.LAST_SYNC_TIME, Date.now())
        set({ xp: res.data.currentXp })
        setStorageData(STORAGE_KEYS.USER_XP, res.data.currentXp)
      }
    } catch (e) {
      console.error('同步历史失败:', e)
    }
  },

  syncWrongBook: async () => {
    // 错题同步 - 从本地存储获取
    const { token } = get()
    if (!token) return

    try {
      const localWrongBook = getStorageData<unknown[]>(STORAGE_KEYS.WRONG_BOOK, [])
      if (localWrongBook.length === 0) return

      await userApi.syncWrongBook(localWrongBook)
    } catch (e) {
      console.error('同步错题失败:', e)
    }
  },
}))
