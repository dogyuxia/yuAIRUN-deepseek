import { PropsWithChildren } from 'react'
import { useLaunch } from '@tarojs/taro'
import './app.scss'

function App({ children }: PropsWithChildren) {
  useLaunch(() => {
    console.log('🚀 AI闯关学园 启动')
  })

  return children
}

export default App
