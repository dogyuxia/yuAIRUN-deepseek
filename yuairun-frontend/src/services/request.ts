/** Taro.request 封装 */
import Taro from '@tarojs/taro'
import { API_BASE_URL } from '../utils/constants'

interface RequestOptions {
  url: string
  method?: 'GET' | 'POST' | 'PUT' | 'DELETE'
  data?: unknown
  timeout?: number
}

export async function request<T>(options: RequestOptions): Promise<T> {
  const { url, method = 'GET', data, timeout = 90000 } = options

  try {
    const response = await Taro.request({
      url: `${API_BASE_URL}${url}`,
      method,
      data: data !== undefined ? JSON.stringify(data) : undefined,
      timeout,
      header: {
        'Content-Type': 'application/json',
      },
    })

    if (response.statusCode >= 200 && response.statusCode < 300) {
      return response.data as T
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
