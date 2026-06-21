/** Taro.request 封装 - 自动注入 Authorization header */
import Taro from '@tarojs/taro'
import { API_BASE_URL, STORAGE_KEYS } from '../utils/constants'
import { getStorageData } from '../utils/storage'

interface RequestOptions {
  url: string
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  data?: unknown
  timeout?: number
}

export async function request<T>(options: RequestOptions): Promise<T> {
  const { url, method = 'GET', data, timeout = 90000 } = options

  // 自动注入 Token
  const token = getStorageData<string | null>(STORAGE_KEYS.TOKEN, null)
  const header: Record<string, string> = {
    'Content-Type': 'application/json',
  }
  if (token) {
    header['Authorization'] = `Bearer ${token}`
  }

  try {
    const response = await Taro.request({
      url: `${API_BASE_URL}${url}`,
      method,
      data: data !== undefined ? JSON.stringify(data) : undefined,
      timeout,
      header,
    })

    if (response.statusCode >= 200 && response.statusCode < 300) {
      return response.data as T
    }

    // 401 Token 过期 - 清除过期 Token 并触发重新登录
    if (response.statusCode === 401) {
      Taro.removeStorageSync(STORAGE_KEYS.TOKEN)
      // 延迟触发静默重新登录（避免阻塞当前请求，使用稳定的 deviceId 恢复会话）
      setTimeout(() => {
        import('../store/userStore').then(({ useUserStore }) => {
          useUserStore.getState().silentLogin()
        })
      }, 100)
    }

    throw new Error(`请求失败: ${response.statusCode}`)
  } catch (error: unknown) {
    if (error instanceof Error) {
      if (error.message.includes('timeout') || error.message.includes('网络')) {
        throw new Error('请求超时，请检查网络后重试')
      }
      throw error
    }
    throw new Error('网络异常，请检查网络后重试')
  }
}
