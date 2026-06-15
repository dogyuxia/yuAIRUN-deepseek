/** 答题结果页 */
import { View, Text, Button } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { useQuizStore } from '../../store/quizStore'
import { useUserStore } from '../../store/userStore'
import { formatDuration } from '../../utils/format'
import type { QuizRecord } from '../../types/quiz'
import { useState, useEffect } from 'react'
import './index.scss'

export default function Result() {
  const { lastRecord, resetQuiz } = useQuizStore()
  const { addHistory, addXp, xp } = useUserStore()

  const [record, setRecord] = useState<QuizRecord | null>(null)

  useEffect(() => {
    if (lastRecord) {
      setRecord(lastRecord)
      addHistory(lastRecord)
      addXp(lastRecord.correctCount * 10)
    }
  }, [])

  if (!record) {
    return (
      <View className='result-page'>
        <View className='gradient-bar' />
        <View style={{ textAlign: 'center', paddingTop: '200px' }}>
          <Text style={{ fontSize: '28px', color: '#A0887E' }}>加载中...</Text>
        </View>
      </View>
    )
  }

  const accuracy = record.accuracy
  const isPass = accuracy >= 0.6
  const emoji = accuracy >= 0.9 ? '🏆' : accuracy >= 0.7 ? '🎉' : accuracy >= 0.5 ? '💪' : '📚'

  const handleViewReport = () => {
    Taro.navigateTo({ url: '/pages/report/index' })
  }

  const handleRetry = () => {
    resetQuiz()
    Taro.navigateBack()
  }

  const handleShare = () => {
    Taro.navigateTo({ url: '/pages/share/index' })
  }

  return (
    <View className='result-page'>
      <View className='gradient-bar' />

      {/* 得分 */}
      <View className='result-score'>
        <View className='result-ring'>{emoji}</View>
        <View className='big-num'>
          {Math.round(accuracy * 100)}<Text className='percent'>%</Text>
        </View>
        <Text className='sub'>
          答对 {record.correctCount} / {record.totalCount} 题 · {isPass ? '闯关成功！' : '继续加油！'}
        </Text>
      </View>

      {/* 统计 */}
      <View className='result-stats'>
        <View className='stat-box'>
          <Text className='num'>{record.correctCount}</Text>
          <Text className='lbl'>✅ 正确</Text>
        </View>
        <View className='stat-box'>
          <Text className='num'>{record.totalCount - record.correctCount}</Text>
          <Text className='lbl'>❌ 错误</Text>
        </View>
        <View className='stat-box'>
          <Text className='num'>{formatDuration(record.duration)}</Text>
          <Text className='lbl'>⏱ 用时</Text>
        </View>
      </View>

      {/* XP 进度 */}
      <View className='result-xp'>
        <Text className='xp-icon'>🏆</Text>
        <View className='xp-info'>
          <Text className='xp-label'>经验值进度</Text>
          <View className='xp-bar'>
            <View className='xp-fill' style={{ width: `${Math.min((xp % 100) / 100 * 100, 100)}%` }} />
          </View>
        </View>
        <Text className='xp-val'>+{record.correctCount * 10}</Text>
      </View>

      {/* 按钮 */}
      <Button className='btn btn-primary' onClick={handleViewReport}>
        📋 查看分析报告
      </Button>

      <View className='result-actions'>
        <Button className='btn btn-outline' onClick={handleRetry}>
          🔄 再来一次
        </Button>
        <Button className='btn btn-outline' onClick={handleShare}>
          📤 分享成果
        </Button>
      </View>
    </View>
  )
}
