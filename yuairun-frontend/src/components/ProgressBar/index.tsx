/** 进度条组件 */
import { View, Text } from '@tarojs/components'
import './index.scss'

interface ProgressBarProps {
  current: number
  total: number
}

export default function ProgressBar({ current, total }: ProgressBarProps) {
  const percent = total > 0 ? (current / total) * 100 : 0

  return (
    <View className='quiz-progress'>
      <Text className='p-icon'>📊</Text>
      <View className='p-bar'>
        <View className='p-fill' style={{ width: `${percent}%` }} />
      </View>
      <Text className='p-text'>
        {current} / {total}
      </Text>
    </View>
  )
}
