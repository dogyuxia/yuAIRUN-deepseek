/** 分析报告相关类型定义 */

/** AI 分析报告数据 */
export interface AnalyzeReportData {
  summary: string
  score: number
  accuracy: number
  weakPoints: string[]
  strongPoints: string[]
  suggestions: string[]
  recommendedTopics: string[]
  detailedAnalysis: string
}
