/** 首页 - 展示 Logo、快捷学科、最近学习 */
import { View, Text, Button } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { useDidShow } from '@tarojs/taro'
import { useUserStore } from '../../store/userStore'
import { SUBJECT_QUICK_OPTIONS } from '../../utils/constants'
import { formatDate, formatPercent } from '../../utils/format'
import type { QuizRecord } from '../../types/quiz'
import './index.scss'

export default function Home() {
  const { history, loadFromStorage } = useUserStore()
  const hour = new Date().getHours()
  const greeting = hour < 12 ? '🌅 早上好' : hour < 18 ? '☀️ 下午好' : '🌙 晚上好'
  const slogan = `${greeting}！输入你想学的，AI 帮你出题闯关`

  useDidShow(() => {
    loadFromStorage()
  })

  const handleStartLearning = () => {
    Taro.navigateTo({ url: '/pages/topic-input/index' })
  }

  const handleQuickSubject = (subject: string) => {
    Taro.navigateTo({
      url: `/pages/topic-input/index?subject=${encodeURIComponent(subject)}`,
    })
  }

  const handleHistoryItem = (record: QuizRecord) => {
    Taro.navigateTo({
      url: `/pages/result/index?history=${encodeURIComponent(JSON.stringify(record))}`,
    })
  }

  const recentHistory = history.slice(0, 5)

  return (
    <View className='home-page'>
      {/* 渐变装饰条 */}
      <View className='gradient-bar' />

      {/* Logo 区域 */}
      <View className='home-logo-area'>
        <View className='logo-icon'>🎯</View>
        <View className='logo-title'>
          <Text className='logo-text'>AI </Text>
          <Text className='logo-text highlight'>闯关</Text>
          <Text className='logo-text'>学园</Text>
        </View>
        <Text className='home-slogan'>
          {greeting}！输入你想学的，AI 帮你出题闯关
        </Text>
      </View>

      {/* 快捷学科卡片 */}
      <View className='home-quick-cards'>
        {SUBJECT_QUICK_OPTIONS.map((item) => (
          <View
            key={item.label}
            className='quick-card'
            onClick={() => handleQuickSubject(item.label)}
          >
            <Text className='qc-icon'>{item.icon}</Text>
            <Text className='qc-label'>{item.label}</Text>
          </View>
        ))}
      </View>

      {/* 开始学习按钮 */}
      <Button className='btn btn-primary' onClick={handleStartLearning}>
        ✏️ 开始学习
      </Button>

      {/* 最近学习 */}
      {recentHistory.length > 0 && (
        <View className='home-recent'>
          <Text className='recent-label'>📌 最近学习</Text>
          {recentHistory.map((item) => (
            <View
              key={item.id}
              className='recent-item'
              onClick={() => handleHistoryItem(item)}
            >
              <View className='item-left'>
                <Text className='item-topic'>{item.topic}</Text>
                <Text className='item-meta'>
                  {item.subject} · {item.totalCount}题
                </Text>
              </View>
              <Text
                className='item-score'
                style={{
                  color: item.accuracy >= 0.8 ? '#6E9B92' : item.accuracy >= 0.6 ? '#C97B6B' : '#D4856C',
                }}
              >
                {formatPercent(item.accuracy)}
              </Text>
            </View>
          ))}
        </View>
      )}

      {/* 空状态 */}
      {recentHistory.length === 0 && (
        <View className='home-empty'>
          <Text className='empty-icon'>📚</Text>
          <Text className='empty-text'>还没有学习记录</Text>
          <Text className='empty-sub'>输入知识点，开始第一次闯关吧！</Text>
        </View>
      )}

      {/* 导航点 */}
      <View className='nav-dots'>
        <View className='dot active' />
        <View className='dot' />
        <View className='dot' />
      </View>
    </View>
  )
}
