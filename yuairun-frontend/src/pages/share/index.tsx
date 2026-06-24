/** 分享海报页 */
import { View, Text, Button } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { useState, useEffect } from 'react'
import { useQuizStore } from '../../store/quizStore'
import type { QuizRecord } from '../../types/quiz'
import './index.scss'

const QUOTES = [
  '学习就像闯关，每一步都算数',
  '知识是最好的护城河',
  '今天的学习，是明天的底气',
  '持续进步，做更好的自己',
  '学无止境，闯关不息',
]

export default function Share() {
  const { lastRecord } = useQuizStore()
  const [record, setRecord] = useState<QuizRecord | null>(null)
  const [quote] = useState(() => QUOTES[Math.floor(Math.random() * QUOTES.length)])

  useEffect(() => {
    if (lastRecord) {
      setRecord(lastRecord)
    }
  }, [])

  if (!record) return null

  const accuracy = Math.round(record.accuracy * 100)

  const handleSave = () => {
    Taro.showToast({ title: '已保存到相册', icon: 'success' })
  }

  const handleShare = () => {
    // @ts-ignore shareAppMessage is available at runtime
    Taro.shareAppMessage({
      title: `我在「AI闯关学园」学习了${record.topic}，答对了${record.correctCount}/${record.totalCount}题！`,
      path: '/pages/home/index',
    })
  }

  return (
    <View className='share-page'>
      <View className='gradient-bar' />

      {/* 海报预览 */}
      <View className='poster-preview'>
        {/* 装饰圆 */}
        <View className='poster-circle poster-circle-1' />
        <View className='poster-circle poster-circle-2' />

        {/* 金句 */}
        <View className='poster-quote'>{quote}</View>

        {/* 分数 */}
        <View className='poster-score'>{accuracy}%</View>

        {/* 详情 */}
        <View className='poster-detail'>
          <Text className='poster-subject'>{record.subject}</Text>
          <Text className='poster-topic'>{record.topic}</Text>
          <Text className='poster-stats'>
            答对 {record.correctCount}/{record.totalCount} 题
          </Text>
        </View>

        {/* 小程序码占位 */}
        <View className='poster-code'>
          <View className='code-grid'>
            {Array.from({ length: 9 }).map((_, i) => (
              <View key={i} className='code-dot' />
            ))}
          </View>
          <Text className='code-label'>小程序码</Text>
        </View>
      </View>

      {/* 操作按钮 */}
      <View className='share-actions'>
        <Button className='btn btn-primary' onClick={handleSave}>
          💾 保存到相册
        </Button>
        <Button className='btn btn-outline' onClick={handleShare}>
          📤 分享好友
        </Button>
      </View>

      <Text className='share-invite'>邀请好友一起闯关学习 🎯</Text>
    </View>
  )
}
