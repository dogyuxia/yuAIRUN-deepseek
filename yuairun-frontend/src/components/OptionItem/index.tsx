/** 选项组件 */
import { View, Text } from '@tarojs/components'
import './index.scss'

interface OptionItemProps {
  label: string
  content: string
  /** 选项状态: normal | selected | correct | wrong */
  status?: 'normal' | 'selected' | 'correct' | 'wrong'
  disabled?: boolean
  onClick?: () => void
}

export default function OptionItem({
  label,
  content,
  status = 'normal',
  disabled = false,
  onClick,
}: OptionItemProps) {
  const classNames = ['opt', status].join(' ')

  return (
    <View className={classNames} onClick={!disabled ? onClick : undefined}>
      <View className='opt-label'>{label}</View>
      <Text className='opt-content'>{content}</Text>
      {status === 'correct' && <Text className='opt-icon'>✅</Text>}
      {status === 'wrong' && <Text className='opt-icon'>❌</Text>}
    </View>
  )
}
