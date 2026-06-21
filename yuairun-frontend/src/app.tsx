import { PropsWithChildren } from 'react'
import { useLaunch } from '@tarojs/taro'
import { useUserStore } from './store/userStore'
import './app.scss'

function App({ children }: PropsWithChildren) {
  useLaunch(() => {
    console.log('🚀 AI闯关学园 启动')

    // 加载本地存储
    useUserStore.getState().loadFromStorage()

    // 静默登录
    setTimeout(() => {
      useUserStore.getState().silentLogin()
    }, 500)
  })

  return children
}

export default App
