/** 题目相关 API */
import { request } from './request'
import type { GenerateQuizRequest, GenerateQuizResponse } from '../types/api'

/** AI 生成题目 */
export async function generateQuiz(params: GenerateQuizRequest): Promise<GenerateQuizResponse> {
  return request<GenerateQuizResponse>({
    url: '/api/quiz/generate',
    method: 'POST',
    data: params,
    timeout: 90000,
  })
}
