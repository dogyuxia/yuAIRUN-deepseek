/** 格式化工具函数 */

/** 格式化时间（秒转为可读格式） */
export function formatDuration(seconds: number): string {
  if (seconds < 60) return `${seconds}秒`
  const min = Math.floor(seconds / 60)
  const sec = seconds % 60
  return sec > 0 ? `${min}分${sec}秒` : `${min}分钟`
}

/** 格式化日期 */
export function formatDate(timestamp: number): string {
  const d = new Date(timestamp)
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hour = String(d.getHours()).padStart(2, '0')
  const min = String(d.getMinutes()).padStart(2, '0')
  return `${month}-${day} ${hour}:${min}`
}

/** 格式化百分比 */
export function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`
}

/** 生成唯一 ID */
export function generateId(): string {
  return Date.now().toString(36) + Math.random().toString(36).substring(2, 8)
}
