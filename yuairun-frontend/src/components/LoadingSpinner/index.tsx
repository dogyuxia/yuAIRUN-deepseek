/** Loading 动画组件（含分阶段进度提示） */
import { View, Text, Button } from '@tarojs/components'
import { useState, useEffect } from 'react'
import './index.scss'

interface LoadingSpinnerProps {
  /** 预计题目数量 */
  questionCount?: number
  /** 取消回调 */
  onCancel?: () => void
}

const STAGES = [
  '🧠 AI 正在分析知识点...',
  '📝 正在生成题目...',
  '✍️ 正在编写解析...',
  '✅ 即将完成...',
]

const FUN_FACTS = [
  '💡 人类大脑有约 860 亿个神经元',
  '💡 光速约为 30 万公里/秒',
  '💡 TCP 协议诞生于 1974 年',
  '💡 Python 是 1991 年发布的',
  '💡 第一个网站发布于 1991 年',
]

export default function LoadingSpinner({ questionCount = 5, onCancel }: LoadingSpinnerProps) {
  const [stageIndex, setStageIndex] = useState(0)
  const [funFact, setFunFact] = useState(FUN_FACTS[0])
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    // 分阶段进度
    const stageTimer = setInterval(() => {
      setStageIndex((prev) => Math.min(prev + 1, STAGES.length - 1))
    }, 8000)

    // 进度条
    const progressTimer = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 90) return prev
        return prev + Math.random() * 3
      })
    }, 1000)

    // 趣味知识轮播
    const funTimer = setInterval(() => {
      setFunFact(FUN_FACTS[Math.floor(Math.random() * FUN_FACTS.length)])
    }, 4000)

    return () => {
      clearInterval(stageTimer)
      clearInterval(progressTimer)
      clearInterval(funTimer)
    }
  }, [])

  return (
    <View className='loading-overlay'>
      <View className='loading-card'>
        <View className='loading-icon'>🤖</View>
        <Text className='loading-title'>AI 正在出题...</Text>

        {/* 进度条 */}
        <View className='loading-bar'>
          <View className='loading-bar-fill' style={{ width: `${Math.min(progress, 95)}%` }} />
        </View>

        {/* 阶段提示 */}
        <View className='loading-stage'>
          {STAGES[stageIndex]}
        </View>

        {/* 已生成进度 */}
        <View className='loading-progress-text'>
          已生成 {Math.floor(progress / 20)} / {questionCount} 题
        </View>

        {/* 趣味知识 */}
        <View className='loading-fun-fact'>
          {funFact}
        </View>

        {/* 取消按钮 */}
        {onCancel && (
          <Button className='loading-cancel' onClick={onCancel}>
            取消
          </Button>
        )}
      </View>
    </View>
  )
}
