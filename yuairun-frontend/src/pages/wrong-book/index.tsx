/** 错题本页 */
import { View, Text, Button, ScrollView } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { useState, useEffect } from 'react'
import { useUserStore } from '../../store/userStore'
import { getWrongBook, markWrongMastered, deleteWrongBook } from '../../services/user'
import type { WrongBookItem } from '../../types/user'
import './index.scss'

export default function WrongBook() {
  const { isLoggedIn } = useUserStore()
  const [items, setItems] = useState<WrongBookItem[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [hasMore, setHasMore] = useState(false)
  const [loading, setLoading] = useState(false)
  const [activeSubject, setActiveSubject] = useState<string | undefined>(undefined)
  const [subjects, setSubjects] = useState<string[]>([])
  const [expandedId, setExpandedId] = useState<string | null>(null)

  const loadData = async (p = 1, subject?: string) => {
    setLoading(true)
    try {
      const res = await getWrongBook(p, 20, subject)
      if (res.success && res.data) {
        if (p === 1) {
          setItems(res.data.items)
        } else {
          setItems((prev) => [...prev, ...res.data!.items])
        }
        setTotal(res.data.total)
        setHasMore(res.data.hasMore)

        // 提取学科列表
        const allSubjects = [...new Set(res.data.items.map((i) => i.subject))]
        setSubjects((prev) => {
          const merged = [...prev, ...allSubjects]
          return [...new Set(merged)]
        })
      }
    } catch (e) {
      console.error('加载错题本失败:', e)
    }
    setLoading(false)
  }

  useEffect(() => {
    loadData(1, activeSubject)
  }, [activeSubject])

  const handleGoBack = () => {
    Taro.navigateBack()
  }

  const handleSubjectFilter = (subject?: string) => {
    setActiveSubject(subject)
    setPage(1)
    setItems([])
  }

  const handleLoadMore = () => {
    const nextPage = page + 1
    setPage(nextPage)
    loadData(nextPage, activeSubject)
  }

  const handleToggleExpand = (id: string) => {
    setExpandedId(expandedId === id ? null : id)
  }

  const handleMarkMastered = async (id: string) => {
    try {
      const res = await markWrongMastered(id)
      if (res.success) {
        setItems((prev) => prev.filter((i) => i.id !== id))
        setTotal((prev) => prev - 1)
      }
    } catch (e) {
      console.error('标记掌握失败:', e)
    }
  }

  const handleDelete = async (id: string) => {
    try {
      const res = await deleteWrongBook(id)
      if (res.success) {
        setItems((prev) => prev.filter((i) => i.id !== id))
        setTotal((prev) => prev - 1)
      }
    } catch (e) {
      console.error('删除错题失败:', e)
    }
  }

  const handleRetryWrong = (item: WrongBookItem) => {
    const question = item.question
    const record = {
      id: `retry_${Date.now()}`,
      subject: item.subject,
      topic: item.topic,
      questions: [question],
      userAnswers: {},
      correctCount: 0,
      totalCount: 1,
      accuracy: 0,
      duration: 0,
      createdAt: Date.now(),
      wrongQuestions: [question],
    }
    Taro.navigateTo({
      url: `/pages/quiz/index?retry=${encodeURIComponent(JSON.stringify(record))}`,
    })
  }

  return (
    <View className='wrongbook-page'>
      {/* 导航栏 */}
      <View className='wb-nav'>
        <View className='nav-back' onClick={handleGoBack}>
          ← 返回
        </View>
        <Text className='nav-title'>错题本</Text>
        <View className='nav-spacer' />
      </View>

      {/* 学科筛选 */}
      <View className='wb-subjects'>
        <ScrollView scrollX className='subjects-scroll'>
          <View
            className={`subject-tag ${activeSubject === undefined ? 'active' : ''}`}
            onClick={() => handleSubjectFilter(undefined)}
          >
            全部
          </View>
          {subjects.map((s) => (
            <View
              key={s}
              className={`subject-tag ${activeSubject === s ? 'active' : ''}`}
              onClick={() => handleSubjectFilter(s)}
            >
              {s}
            </View>
          ))}
        </ScrollView>
      </View>

      {/* 总数 */}
      <Text className='wb-count'>共 {total} 道错题</Text>

      {/* 错题列表 */}
      <ScrollView className='wb-list' scrollY>
        {items.map((item) => (
          <View key={item.id} className='wb-item'>
            <View className='wb-item-header' onClick={() => handleToggleExpand(item.id)}>
              <Text className='wb-wrong-icon'>❌</Text>
              <View className='wb-item-info'>
                <Text className='wb-question-text'>{item.question.question}</Text>
                <Text className='wb-type'>{item.question.type === 'single' ? '单选题' : item.question.type === 'multiple' ? '多选题' : '判断题'}</Text>
              </View>
            </View>

            {expandedId === item.id && (
              <View className='wb-item-detail'>
                <View className='wb-answer-info'>
                  <Text className='wb-user-answer'>你的答案: <Text className='wrong-answer'>{item.userAnswer}</Text></Text>
                  <Text className='wb-correct-answer'>正确答案: <Text className='correct-answer'>{item.correctAnswer}</Text></Text>
                </View>
                <Text className='wb-explanation'>{item.question.explanation}</Text>
                <View className='wb-actions'>
                  <Button className='wb-btn wb-btn-explain' onClick={() => handleToggleExpand(item.id)}>
                    📖 收起解析
                  </Button>
                  <Button className='wb-btn wb-btn-retry' onClick={() => handleRetryWrong(item)}>
                    🔄 重新练习
                  </Button>
                  <Button className='wb-btn wb-btn-master' onClick={() => handleMarkMastered(item.id)}>
                    ✅ 已掌握
                  </Button>
                </View>
              </View>
            )}

            {expandedId !== item.id && (
              <View className='wb-item-preview'>
                <Text className='wb-preview-answer'>你的答案: {item.userAnswer}</Text>
                <Text className='wb-preview-correct'>正确答案: {item.correctAnswer}</Text>
                <View className='wb-preview-actions'>
                  <Button className='wb-mini-btn' onClick={() => handleToggleExpand(item.id)}>📖 查看解析</Button>
                  <Button className='wb-mini-btn' onClick={() => handleRetryWrong(item)}>🔄 重新练习</Button>
                </View>
              </View>
            )}
          </View>
        ))}

        {loading && (
          <Text className='wb-loading'>加载中...</Text>
        )}

        {hasMore && !loading && (
          <Button className='wb-load-more' onClick={handleLoadMore}>
            加载更多
          </Button>
        )}

        {!hasMore && items.length > 0 && (
          <Text className='wb-no-more'>-- 没有更多了 --</Text>
        )}

        {!loading && items.length === 0 && (
          <View className='wb-empty'>
            <Text className='empty-icon'>🎉</Text>
            <Text className='empty-text'>暂无错题，继续保持！</Text>
          </View>
        )}
      </ScrollView>
    </View>
  )
}
