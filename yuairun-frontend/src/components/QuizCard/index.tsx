/** 题目卡片组件 */
import { View, Text } from '@tarojs/components'
import OptionItem from '../OptionItem/index'
import type { QuizQuestion } from '../../types/quiz'
import { getKnowledgeSourceLabel } from '../../types/quiz'
import './index.scss'

interface QuizCardProps {
  question: QuizQuestion
  userAnswer?: string | string[]
  showResult?: boolean
  onSelect?: (answer: string | string[]) => void
}

const TYPE_LABELS: Record<string, string> = {
  single: '📌 单选题',
  multiple: '📌 多选题',
  judge: '📌 判断题',
}

function isCorrect(q: QuizQuestion, userAns: string | string[] | undefined): boolean {
  if (!userAns) return false
  if (Array.isArray(q.answer)) {
    return Array.isArray(userAns) && JSON.stringify([...userAns].sort()) === JSON.stringify([...q.answer].sort())
  }
  return String(userAns) === String(q.answer)
}

export default function QuizCard({ question, userAnswer, showResult = false, onSelect }: QuizCardProps) {
  const q = question
  const answered = userAnswer !== undefined
  const isAnsCorrect = answered ? isCorrect(q, userAnswer) : false

  const getOptionStatus = (label: string): 'normal' | 'correct' | 'wrong' => {
    if (!showResult || !answered) return 'normal'

    const isSelected = Array.isArray(userAnswer)
      ? userAnswer.includes(label)
      : userAnswer === label

    const isCorrectAns = Array.isArray(q.answer)
      ? q.answer.includes(label)
      : q.answer === label

    if (isCorrectAns) return 'correct'
    if (isSelected && !isCorrectAns) return 'wrong'
    return 'normal'
  }

  const handleSelect = (label: string) => {
    if (showResult || answered) return
    if (q.type === 'multiple') {
      const current = (Array.isArray(userAnswer) ? [...userAnswer] : []) as string[]
      const idx = current.indexOf(label)
      if (idx >= 0) {
        current.splice(idx, 1)
      } else {
        current.push(label)
      }
      onSelect?.(current)
    } else {
      onSelect?.(label)
    }
  }

  const sourceTag = getKnowledgeSourceLabel(q.knowledgeSource)

  return (
    <View className='quiz-card'>
      {/* 题目头部：题目标签 + 来源标签 */}
      <View className='quiz-card-header'>
        <Text className='q-tag'>{TYPE_LABELS[q.type] || '📌 题目'}</Text>
        <Text className={`q-source-tag ${q.knowledgeSource === 'knowledge_base' ? 'kb' : 'ai'}`}>
          {sourceTag}
        </Text>
      </View>
      {/* 题目 */}
      <View className='quiz-question-box'>
        <Text className='q-text'>{q.question}</Text>
      </View>

      {/* 选项 */}
      <View className='quiz-options'>
        {q.options.map((opt) => (
          <OptionItem
            key={opt.label}
            label={opt.label}
            content={opt.content}
            status={getOptionStatus(opt.label)}
            disabled={showResult || answered}
            onClick={() => handleSelect(opt.label)}
          />
        ))}
      </View>

      {/* 反馈区域 */}
      {showResult && answered && (
        <View className={`quiz-feedback ${isAnsCorrect ? 'correct' : 'wrong'}`}>
          <View className='fb-title'>
            {isAnsCorrect ? '✅' : '❌'}{' '}
            <Text style={{ color: isAnsCorrect ? '#6E9B92' : '#D4856C' }}>
              {isAnsCorrect ? '回答正确！+10 XP' : '回答错误'}
            </Text>
          </View>
          <View className='fb-body'>{q.explanation}</View>
        </View>
      )}
    </View>
  )
}
