/** 内容输入页 - 用户输入知识点 */
import { View, Text, Textarea, Button, Input } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { useState } from 'react'
import { useQuizStore } from '../../store/quizStore'
import { useUserStore } from '../../store/userStore'
import { generateQuiz } from '../../services/quiz'
import LoadingSpinner from '../../components/LoadingSpinner/index'
import { QUIZ_COUNT_OPTIONS, DIFFICULTY_OPTIONS } from '../../utils/constants'
import './index.scss'

export default function TopicInput() {
  const { setQuizData, setLoading, setError } = useQuizStore()
  const { setLastSubject } = useUserStore()

  const [topic, setTopic] = useState('')
  const [subject, setSubject] = useState('')
  const [count, setCount] = useState(5)
  const [difficulty, setDifficulty] = useState('medium')
  const [isLoading, setIsLoading] = useState(false)

  const handleGenerate = async () => {
    if (!topic.trim()) {
      Taro.showToast({ title: '请输入知识点', icon: 'none' })
      return
    }
    if (!subject.trim()) {
      Taro.showToast({ title: '请输入学科类别', icon: 'none' })
      return
    }

    setIsLoading(true)
    setLoading(true)
    setLastSubject(subject)

    try {
      const response = await generateQuiz({
        subject,
        topic: topic.trim(),
        count,
        difficulty,
        type: 'single',
      })

      if (response.success && response.data) {
        setQuizData(response.data.questions, subject, topic.trim())
        Taro.navigateTo({ url: '/pages/quiz/index' })
      } else {
        setError(response.error || '生成失败')
        Taro.showToast({ title: response.error || '生成失败', icon: 'none' })
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : '网络异常'
      setError(msg)
      Taro.showToast({ title: msg, icon: 'none' })
    } finally {
      setIsLoading(false)
      setLoading(false)
    }
  }

  return (
    <View className='topic-input-page'>
      {/* 渐变装饰条 */}
      <View className='gradient-bar' />

      {/* AI 打招呼 */}
      <View className='input-top'>
        <View className='avatar'>😊</View>
        <View className='ai-greeting'>
          <Text className='greeting-text'>今天想学什么？</Text>
          <Text className='greeting-sub'>输入你想了解的知识点，AI 帮你出题闯关</Text>
        </View>
      </View>

      {/* 输入方式选择 */}
      <View className='input-options'>
        <View className='chip active'>📝 自由输入</View>
        <View className='chip'>🔗 粘贴链接</View>
        <View className='chip'>📄 上传文档</View>
      </View>

      {/* 学科输入 */}
      <View className='input-field'>
        <Text className='field-label'>📂 学科类别</Text>
        <Input
          className='input-box subject-input'
          placeholder='例如：计算机网络、Python、高等数学'
          value={subject}
          onInput={(e) => setSubject(e.detail.value)}
          maxlength={50}
        />
      </View>

      {/* 内容输入 */}
      <View className='input-field'>
        <Text className='field-label'>📝 知识点内容</Text>
        <Textarea
          className='input-area'
          placeholder='例如：TCP 三次握手的过程和原理…'
          value={topic}
          onInput={(e) => setTopic(e.detail.value)}
          maxlength={500}
          rows={4}
        />
        <Text className='input-tip'>已输入 {topic.length} 字，建议 10~200 字</Text>
      </View>

      {/* 题目配置 */}
      <View className='config-row'>
        <View className='config-group'>
          <Text className='config-label'>题目数量</Text>
          <View className='tag-group'>
            {QUIZ_COUNT_OPTIONS.map((n) => (
              <Text
                key={n}
                className={`tag ${count === n ? 'tag-red' : 'tag-warm'}`}
                onClick={() => setCount(n)}
              >
                {n}题
              </Text>
            ))}
          </View>
        </View>
        <View className='config-group'>
          <Text className='config-label'>难度</Text>
          <View className='tag-group'>
            {DIFFICULTY_OPTIONS.map((d) => (
              <Text
                key={d.value}
                className={`tag ${difficulty === d.value ? 'tag-teal' : 'tag-warm'}`}
                onClick={() => setDifficulty(d.value)}
              >
                {d.label}
              </Text>
            ))}
          </View>
        </View>
      </View>

      {/* 生成按钮 */}
      <Button
        className='btn btn-primary generate-btn'
        onClick={handleGenerate}
        loading={isLoading}
      >
        🤖 AI 生成题目
      </Button>

      {/* Loading */}
      {isLoading && (
        <LoadingSpinner questionCount={count} onCancel={() => setIsLoading(false)} />
      )}
    </View>
  )
}
