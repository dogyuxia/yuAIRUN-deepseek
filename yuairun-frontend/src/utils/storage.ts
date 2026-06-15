/** 本地存储封装 */
import Taro from '@tarojs/taro'

export function getStorageData<T>(key: string, defaultValue: T): T {
  try {
    const value = Taro.getStorageSync(key)
    return value || defaultValue
  } catch {
    return defaultValue
  }
}

export function setStorageData<T>(key: string, value: T): void {
  try {
    Taro.setStorageSync(key, value)
  } catch (e) {
    console.error('存储失败:', key, e)
  }
}

export function removeStorageData(key: string): void {
  try {
    Taro.removeStorageSync(key)
  } catch (e) {
    console.error('删除存储失败:', key, e)
  }
}
