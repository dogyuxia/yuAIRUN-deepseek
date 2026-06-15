/** AI 分析报告页 */
import { View, Text, Button } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { useState, useEffect } from 'react'
import { analyzeQuiz } from '../../services/report'
import { useQuizStore } from '../../store/quizStore'
import type { QuizRecord } from '../../types/quiz'
import type { AnalyzeReportData } from '../../types/report'
import './index.scss'

export default function Report() {
  const { lastRecord } = useQuizStore()
  const [report, setReport] = useState<AnalyzeReportData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [record, setRecord] = useState<QuizRecord | null>(null)

  useEffect(() => {
    if (lastRecord) {
      setRecord(lastRecord)
      fetchReport(lastRecord)
    } else {
      setError('未找到答题数据')
      setLoading(false)
    }
  }, [])

  const fetchReport = async (record: QuizRecord) => {
    try {
      const response = await analyzeQuiz({
        subject: record.subject,
        topic: record.topic,
        questions: record.questions,
        userAnswers: record.userAnswers,
        duration: record.duration,
      })

      if (response.success && response.data) {
        setReport(response.data)
      } else {
        setError(response.error || '生成报告失败')
      }
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : '网络异常')
    } finally {
      setLoading(false)
    }
  }

  const handleShare = () => {
    Taro.navigateTo({ url: '/pages/share/index' })
  }

  if (loading) {
    return (
      <View className='report-page'>
        <View className='report-loading'>
          <Text className='loading-icon'>🧠</Text>
          <Text className='loading-text'>AI 正在分析你的答题数据...</Text>
        </View>
      </View>
    )
  }

  if (error) {
    return (
      <View className='report-page'>
        <View className='report-error'>
          <Text className='error-icon'>😅</Text>
          <Text className='error-text'>{error}</Text>
          <Button className='btn btn-outline' onClick={() => record && fetchReport(record)}>
            重新生成
          </Button>
        </View>
      </View>
    )
  }

  if (!report || !record) return null

  return (
    <View className='report-page'>
      <View className='gradient-bar' />

      {/* 报告头部 */}
      <View className='report-header'>
        <View className='rh-avatar'>🧠</View>
        <View className='rh-text'>
          <Text className='rh-name'>AI 学习教练</Text>
          <Text className='rh-sub'>基于你的答题数据生成</Text>
        </View>
        <Text className='rh-icon'>🤖</Text>
      </View>

      {/* 整体评估 */}
      <View className='report-section'>
        <Text className='rs-title'>📌 整体评估</Text>
        <View className='rs-body'>{report.summary}</View>
      </View>

      {/* 掌握较好 */}
      {report.strongPoints.length > 0 && (
        <View className='report-section'>
          <Text className='rs-title'>💪 掌握较好</Text>
          <View className='rs-body'>
            {report.strongPoints.map((point, i) => (
              <Text key={i} className='strong-tag'>{point}</Text>
            ))}
          </View>
        </View>
      )}

      {/* 需要加强 */}
      {report.weakPoints.length > 0 && (
        <View className='report-section'>
          <Text className='rs-title'>📌 需要加强</Text>
          <View className='rs-body'>
            {report.weakPoints.map((point, i) => (
              <Text key={i} className='weak-tag'>{point}</Text>
            ))}
          </View>
        </View>
      )}

      {/* 学习建议 */}
      <View className='report-section'>
        <Text className='rs-title'>💡 学习建议</Text>
        <View className='rs-body'>
          {report.suggestions.map((s, i) => (
            <Text key={i} className='suggestion-line'>{i + 1}. {s}</Text>
          ))}
        </View>
      </View>

      {/* 推荐练习 */}
      {report.recommendedTopics.length > 0 && (
        <View className='report-section'>
          <Text className='rs-title'>🎯 推荐练习</Text>
          <View className='rs-body'>
            {report.recommendedTopics.map((topic, i) => (
              <Text key={i} className='rec-tag'>{topic}</Text>
            ))}
          </View>
        </View>
      )}

      <Button className='btn btn-primary share-btn' onClick={handleShare}>
        📤 生成分享海报
      </Button>
    </View>
  )
}
