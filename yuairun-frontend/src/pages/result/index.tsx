/** 答题结果页 */
import { View, Text, Button } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { useQuizStore } from '../../store/quizStore'
import { useUserStore } from '../../store/userStore'
import { formatDuration } from '../../utils/format'
import { STORAGE_KEYS } from '../../utils/constants'
import { getStorageData, setStorageData } from '../../utils/storage'
import type { QuizRecord } from '../../types/quiz'
import { useState, useEffect, useRef } from 'react'
import './index.scss'

export default function Result() {
  const { lastRecord, resetQuiz } = useQuizStore()
  const { addHistory, addXp, xp, syncHistory, syncWrongBook, loadUserProfile, isLoggedIn } = useUserStore()

  const [record, setRecord] = useState<QuizRecord | null>(null)
  const [isViewMode, setIsViewMode] = useState(false)
  const syncedRef = useRef(false)
  const freshRecordRef = useRef<QuizRecord | null>(null)

  // 计算本次获得经验值（与后端 calculate_xp_earned 保持一致）
  const calcXpEarned = (correctCount: number, totalCount: number) => {
    let earned = correctCount * 10
    if (correctCount >= 2) earned += (correctCount - 1) * 5
    if (correctCount === totalCount && totalCount > 0) earned += 20
    return earned
  }

  useEffect(() => {
    // 先检查 URL 参数：从首页「最近学习」点击查看
    const params = Taro.getCurrentInstance().router?.params
    const hasUrlHistory = params?.history

    if (hasUrlHistory) {
      // 查看历史记录模式——不调用 addHistory/addXp，避免重复
      try {
        const decoded: QuizRecord = JSON.parse(decodeURIComponent(params.history as string))
        setRecord(decoded)
        setIsViewMode(true)
      } catch (e) {
        console.error('解析历史记录参数失败:', e)
      }
      return
    }

    // 无 URL 参数且 lastRecord 存在 → 刚完成答题跳转过来
    if (lastRecord) {
      setRecord(lastRecord)
      setIsViewMode(false)
      // 保存到 ref 供后续同步使用（resetQuiz 会清空 lastRecord）
      freshRecordRef.current = lastRecord
      addHistory(lastRecord)
      const earned = calcXpEarned(lastRecord.correctCount, lastRecord.totalCount)
      addXp(earned)

      // 将错题保存到本地错题本存储（用于后续同步）
      if (lastRecord.wrongQuestions && lastRecord.wrongQuestions.length > 0) {
        const existingWrong = getStorageData<any[]>(STORAGE_KEYS.WRONG_BOOK, [])
        const newWrongItems = lastRecord.wrongQuestions.map((q) => ({
          question: q,
          userAnswer: typeof lastRecord.userAnswers[q.id] === 'object'
            ? (lastRecord.userAnswers[q.id] as string[]).join(', ')
            : String(lastRecord.userAnswers[q.id] || ''),
          correctAnswer: Array.isArray(q.answer) ? q.answer.join(', ') : String(q.answer),
          subject: lastRecord.subject,
          topic: lastRecord.topic,
        }))
        const merged = [...newWrongItems, ...existingWrong].slice(0, 100)
        setStorageData(STORAGE_KEYS.WRONG_BOOK, merged)
      }

      // 消费完后清除 lastRecord，防止下次以 URL 参数进入时再次处理
      resetQuiz()
    }
  }, [])

  // 答题完成后同步到云端（仅首次答题完成时执行，查看历史时不执行）
  useEffect(() => {
    if (freshRecordRef.current && isLoggedIn && !syncedRef.current) {
      syncedRef.current = true
      // 延迟同步，避免阻塞页面渲染
      setTimeout(() => {
        syncHistory().catch(() => {})
        syncWrongBook().catch(() => {})
        // 同步后刷新个人中心数据
        setTimeout(() => loadUserProfile().catch(() => {}), 500)
      }, 300)
    }
  }, [isLoggedIn])

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
    // 跳转到出题页面，而非返回（避免卡在空白答题页）
    Taro.redirectTo({ url: '/pages/topic-input/index' })
  }

  const handleGoHome = () => {
    resetQuiz()
    Taro.redirectTo({ url: '/pages/home/index' })
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
        <Text className='xp-val'>+{calcXpEarned(record.correctCount, record.totalCount)}</Text>
      </View>

      {/* 按钮 */}
      <Button className='btn btn-primary' onClick={handleViewReport}>
        📋 查看分析报告
      </Button>

      <Button className='btn btn-outline' onClick={handleGoHome}>
        🏠 返回首页
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
