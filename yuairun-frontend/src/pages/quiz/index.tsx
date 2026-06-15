/** 闯关答题页 */
import { View, Text, Button } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { useQuizStore } from '../../store/quizStore'
import { useUserStore } from '../../store/userStore'
import ProgressBar from '../../components/ProgressBar/index'
import QuizCard from '../../components/QuizCard/index'
import './index.scss'

export default function Quiz() {
  const {
    questions, currentIndex, userAnswers, startTime,
    submitAnswer, nextQuestion, finishQuiz,
  } = useQuizStore()
  const { addXp } = useUserStore()

  const currentQ = questions[currentIndex]
  const isAllAnswered = questions.every((q) => userAnswers[q.id] !== undefined)
  const currentAnswer = userAnswers[currentQ?.id]
  const answeredCount = Object.keys(userAnswers).length

  const handleSelect = (answer: string | string[]) => {
    submitAnswer(currentQ.id, answer)
    addXp(10)
  }

  const handleNext = () => {
    if (currentIndex < questions.length - 1) {
      nextQuestion()
    } else {
      handleFinish()
    }
  }

  const handleFinish = () => {
    const record = finishQuiz()
    Taro.navigateTo({ url: '/pages/result/index' })
  }

  if (!questions.length) {
    return (
      <View className='quiz-page'>
        <View className='gradient-bar' />
        <View style={{ textAlign: 'center', paddingTop: '200px' }}>
          <Text style={{ fontSize: '28px', color: '#A0887E' }}>加载中...</Text>
        </View>
      </View>
    )
  }

  return (
    <View className='quiz-page'>
      {/* 渐变条 */}
      <View className='gradient-bar' />

      {/* 进度 */}
      <ProgressBar current={answeredCount} total={questions.length} />

      {/* 题目 */}
      <QuizCard
        question={currentQ}
        userAnswer={currentAnswer}
        showResult={currentAnswer !== undefined}
        onSelect={handleSelect}
      />

      {/* 下一题/完成按钮 */}
      {currentAnswer !== undefined && (
        <Button className='btn btn-primary next-btn' onClick={handleNext}>
          {currentIndex < questions.length - 1 ? '下一题 →' : '查看结果 →'}
        </Button>
      )}

      {/* XP 显示 */}
      <View className='quiz-xp-bar'>
        <View className='xp-stars'>
          {[1, 2, 3, 4, 5].map((star) => (
            <Text key={star} className={`star ${answeredCount >= star ? 'filled' : 'empty'}`}>
              ⭐
            </Text>
          ))}
        </View>
        <Text className='xp-text'>经验值 · {answeredCount * 10} XP</Text>
      </View>
    </View>
  )
}
