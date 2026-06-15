/** 分析报告相关 API */
import { request } from './request'
import type { AnalyzeQuizRequest, AnalyzeQuizResponse } from '../types/api'

/** AI 生成分析报告 */
export async function analyzeQuiz(params: AnalyzeQuizRequest): Promise<AnalyzeQuizResponse> {
  return request<AnalyzeQuizResponse>({
    url: '/api/quiz/analyze',
    method: 'POST',
    data: params,
    timeout: 90000,
  })
}
