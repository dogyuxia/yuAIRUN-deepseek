/** 登录页 - 用户名+密码登录 / 微信一键登录 */
import { View, Text, Input, Button } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { useState } from 'react'
import { useUserStore } from '../../store/userStore'
import './index.scss'

export default function Login() {
  const { manualLogin, login, isLoginLoading, silentLogin } = useUserStore()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  const handleManualLogin = async () => {
    setError('')

    if (username.length !== 6) {
      setError('用户名必须为6位')
      return
    }
    if (password.length !== 6) {
      setError('密码必须为6位')
      return
    }

    const ok = await manualLogin(username, password)
    if (ok) {
      Taro.showToast({ title: '登录成功', icon: 'success' })
      Taro.navigateBack()
    } else {
      setError('登录失败，请检查用户名和密码')
    }
  }

  const handleWechatLogin = async () => {
    setError('')
    try {
      const { code } = await Taro.login()
      const ok = await login(code)
      if (ok) {
        Taro.showToast({ title: '微信登录成功', icon: 'success' })
        Taro.navigateBack()
      } else {
        setError('微信登录失败')
      }
    } catch (e) {
      setError('微信登录失败，请重试')
    }
  }

  const handleGoBack = () => {
    Taro.navigateBack()
  }

  return (
    <View className='login-page'>
      {/* 导航栏 */}
      <View className='login-nav'>
        <View className='nav-back' onClick={handleGoBack}>
          ← 返回
        </View>
        <Text className='nav-title'>登录</Text>
        <View className='nav-spacer' />
      </View>

      {/* 登录卡片 */}
      <View className='login-card'>
        <View className='login-header'>
          <Text className='login-icon'>🔐</Text>
          <Text className='login-title'>欢迎回来</Text>
          <Text className='login-subtitle'>输入账号密码登录，未注册将自动创建</Text>
        </View>

        {/* 用户名输入 */}
        <View className='login-field'>
          <Text className='field-icon'>👤</Text>
          <Input
            className='field-input'
            placeholder='6位用户名'
            value={username}
            onInput={(e) => setUsername(e.detail.value)}
            maxlength={6}
          />
        </View>

        {/* 密码输入 */}
        <View className='login-field'>
          <Text className='field-icon'>🔑</Text>
          <Input
            className='field-input'
            placeholder='6位密码'
            password
            value={password}
            onInput={(e) => setPassword(e.detail.value)}
            maxlength={6}
          />
        </View>

        {/* 错误提示 */}
        {error && <Text className='login-error'>{error}</Text>}

        {/* 登录按钮 */}
        <Button
          className='btn btn-primary login-btn'
          onClick={handleManualLogin}
          loading={isLoginLoading}
        >
          登 录
        </Button>

        <Text className='login-hint'>未注册将自动创建账号</Text>

        {/* 分割线 */}
        <View className='login-divider'>
          <View className='divider-line' />
          <Text className='divider-text'>其他方式</Text>
          <View className='divider-line' />
        </View>

        {/* 微信登录 */}
        <Button
          className='btn btn-wechat'
          onClick={handleWechatLogin}
        >
          💬 微信一键登录
        </Button>
      </View>
    </View>
  )
}
