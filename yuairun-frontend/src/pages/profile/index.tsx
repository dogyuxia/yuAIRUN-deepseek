/** 个人中心页 */
import { View, Text, Button, Image, ScrollView } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { useDidShow } from '@tarojs/taro'
import { useUserStore } from '../../store/userStore'
import { formatDuration, formatPercent, formatDate } from '../../utils/format'
import './index.scss'

export default function Profile() {
  const {
    userInfo,
    isLoggedIn,
    profile,
    loadUserProfile,
    xp,
    logout,
  } = useUserStore()

  useDidShow(() => {
    if (isLoggedIn) {
      loadUserProfile()
    }
  })

  const handleGoBack = () => {
    Taro.navigateBack()
  }

  const handleGoWrongBook = () => {
    Taro.navigateTo({ url: '/pages/wrong-book/index' })
  }

  const handleShare = () => {
    Taro.shareAppMessage({
      title: 'AI闯关学园 - 用AI出题，快乐闯关学习',
    })
  }

  const handleGoLogin = () => {
    Taro.navigateTo({ url: '/pages/login/index' })
  }

  const handleLogout = () => {
    Taro.showModal({
      title: '提示',
      content: '确定要退出登录吗？',
      success: (res) => {
        if (res.confirm) {
          logout()
          Taro.showToast({ title: '已退出登录', icon: 'none' })
        }
      },
    })
  }

  const getLevelProgress = () => {
    const thresholds = [0, 100, 300, 600, 1000, 2000]
    const level = userInfo?.level || 1
    const currentThreshold = thresholds[level - 1] || 0
    const nextThreshold = thresholds[level] || currentThreshold + 1000
    const progress = nextThreshold > currentThreshold
      ? Math.min((xp - currentThreshold) / (nextThreshold - currentThreshold) * 100, 100)
      : 100
    return { progress, nextThreshold, currentThreshold }
  }

  const levelProgress = getLevelProgress()
  const stats = profile?.stats
  const recentHistories = profile?.recentHistories || []

  const menuItems = [
    { icon: '📕', label: '错题本', onClick: handleGoWrongBook },
    { icon: '📤', label: '分享给好友', onClick: handleShare },
  ]

  return (
    <View className='profile-page'>
      {/* 导航栏 */}
      <View className='profile-nav'>
        <View className='nav-back' onClick={handleGoBack}>
          ← 返回
        </View>
        <Text className='nav-title'>个人中心</Text>
        <View className='nav-spacer' />
      </View>

      <ScrollView className='profile-content' scrollY>
        {/* 用户信息区 */}
        <View className='profile-user'>
          <View className='user-avatar'>
            {userInfo?.avatarUrl ? (
              <Image src={userInfo.avatarUrl} mode='aspectFill' className='avatar-img' />
            ) : (
              <Text className='avatar-emoji'>🧑</Text>
            )}
          </View>
          <Text className='user-name'>{userInfo?.nickname || '未登录'}</Text>
          {isLoggedIn && (
            <>
              <Text className='user-level'>
                📚 Lv.{userInfo?.level} {userInfo?.levelTitle}
              </Text>
              <View className='xp-bar-container'>
                <View className='xp-bar'>
                  <View
                    className='xp-fill'
                    style={{ width: `${levelProgress.progress}%` }}
                  />
                </View>
                <Text className='xp-text'>
                  {xp} / {levelProgress.nextThreshold} XP
                </Text>
              </View>
            </>
          )}
        </View>

        {isLoggedIn && stats && (
          <>
            {/* 学习概览 */}
            <View className='profile-section'>
              <Text className='section-title'>📊 学习概览</Text>
              <View className='stats-grid'>
                <View className='stat-card'>
                  <Text className='stat-num'>{stats.totalQuizzes}</Text>
                  <Text className='stat-label'>总闯关</Text>
                </View>
                <View className='stat-card'>
                  <Text className='stat-num'>{stats.totalQuestions}</Text>
                  <Text className='stat-label'>总题数</Text>
                </View>
                <View className='stat-card'>
                  <Text className='stat-num'>{formatPercent(stats.accuracy)}</Text>
                  <Text className='stat-label'>正确率</Text>
                </View>
                <View className='stat-card'>
                  <Text className='stat-num'>{stats.streakDays}天</Text>
                  <Text className='stat-label'>学习天数</Text>
                </View>
                <View className='stat-card'>
                  <Text className='stat-num'>{stats.totalWrong}</Text>
                  <Text className='stat-label'>错题数</Text>
                </View>
                <View className='stat-card'>
                  <Text className='stat-num'>{stats.streakDays}</Text>
                  <Text className='stat-label'>连胜</Text>
                </View>
              </View>
            </View>

            {/* 最近闯关 */}
            {recentHistories.length > 0 && (
              <View className='profile-section'>
                <Text className='section-title'>📌 最近闯关</Text>
                {recentHistories.map((h) => (
                  <View key={h.id} className='recent-item'>
                    <View className='recent-left'>
                      <Text className='recent-topic'>{h.topic}</Text>
                      <Text className='recent-meta'>
                        {h.subject} · {formatDuration(h.duration)}
                      </Text>
                    </View>
                    <Text
                      className='recent-score'
                      style={{
                        color: h.accuracy >= 0.8 ? '#6E9B92' : h.accuracy >= 0.6 ? '#C97B6B' : '#D4856C',
                      }}
                    >
                      {formatPercent(h.accuracy)}
                    </Text>
                  </View>
                ))}
              </View>
            )}
          </>
        )}

        {!isLoggedIn && (
          <View className='profile-login-tip' onClick={handleGoLogin}>
            <Text className='tip-icon'>🔓</Text>
            <Text className='tip-text'>登录后可查看学习数据</Text>
            <View className='btn btn-primary login-entry-btn'>
              去登录
            </View>
          </View>
        )}

        {/* 功能入口 */}
        <View className='profile-section'>
          <Text className='section-title'>📋 功能入口</Text>
          {menuItems.map((item, i) => (
            <View key={i} className='menu-item' onClick={item.onClick}>
              <View className='menu-left'>
                <Text className='menu-icon'>{item.icon}</Text>
                <Text className='menu-label'>{item.label}</Text>
              </View>
              <Text className='menu-arrow'>→</Text>
            </View>
          ))}
        </View>

        {/* 退出登录 */}
        {isLoggedIn && (
          <View className='logout-section'>
            <View className='btn logout-btn' onClick={handleLogout}>
              退出登录
            </View>
          </View>
        )}
      </ScrollView>
    </View>
  )
}
