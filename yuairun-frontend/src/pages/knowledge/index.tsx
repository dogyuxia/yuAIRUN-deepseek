/** 知识库列表页面 */
import { View, Text, Button, ScrollView } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { useState, useEffect } from 'react'
import { getKnowledgeBases, deleteKnowledgeBase, createKnowledgeBase } from '../../services/knowledge'
import type { KnowledgeBase } from '../../types/knowledge'
import './index.scss'

export default function KnowledgePage() {
  const [bases, setBases] = useState<KnowledgeBase[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadKnowledgeBases()
  }, [])

  const loadKnowledgeBases = async () => {
    setLoading(true)
    try {
      const res = await getKnowledgeBases()
      if (res.success) {
        setBases(res.data)
      }
    } catch (e) {
      console.error('加载知识库失败', e)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = () => {
    Taro.showModal({
      title: '创建知识库',
      content: '',
      editable: true,
      placeholderText: '例如：计算机网络复习',
      success: (res: Taro.showModal.SuccessCallbackResult & { content?: string }) => {
        const r = res
        if (r.confirm && r.content) {
          createKnowledgeBase({ name: r.content }).then((result) => {
            if (result.success) {
              Taro.showToast({ title: '创建成功', icon: 'success' })
              loadKnowledgeBases()
            } else {
              Taro.showToast({ title: result.error || '创建失败', icon: 'none' })
            }
          })
        }
      },
    } as any)
  }

  const handleDelete = (kb: KnowledgeBase) => {
    if (kb.isSystem) {
      Taro.showToast({ title: '系统知识库不能删除', icon: 'none' })
      return
    }
    Taro.showModal({
      title: '删除知识库',
      content: `确定要删除"${kb.name}"吗？文档将被一并删除。`,
      success: async (res) => {
        if (res.confirm) {
          const result = await deleteKnowledgeBase(kb.id)
          if (result.success) {
            Taro.showToast({ title: '已删除', icon: 'success' })
            loadKnowledgeBases()
          } else {
            Taro.showToast({ title: result.error || '删除失败', icon: 'none' })
          }
        }
      },
    })
  }

  const handleGoDetail = (kb: KnowledgeBase) => {
    Taro.navigateTo({
      url: `/pages/knowledge-detail/index?kbId=${kb.id}&name=${encodeURIComponent(kb.name)}`,
    })
  }

  const handleGoHome = () => {
    Taro.redirectTo({ url: '/pages/home/index' })
  }

  return (
    <View className='knowledge-page'>
      <View className='gradient-bar' />

      {/* 导航 */}
      <View className='kb-nav'>
        <View className='nav-back' onClick={handleGoHome}>← 返回首页</View>
        <Text className='nav-title'>知识库</Text>
        <View className='nav-spacer' />
      </View>

      {/* 新建知识库入口卡片 */}
      <View className='kb-create-card' onClick={handleCreate}>
        <Text className='create-icon'>➕</Text>
        <View className='create-info'>
          <Text className='create-title'>新建知识库</Text>
          <Text className='create-desc'>上传文档，构建专属知识库</Text>
        </View>
        <Text className='create-arrow'>→</Text>
      </View>

      {/* 列表 */}
      <ScrollView className='kb-list' scrollY>
        {loading ? (
          <View className='loading-state'>
            {[1, 2, 3].map((i) => (
              <View key={i} className='skeleton-card' />
            ))}
          </View>
        ) : bases.length === 0 ? (
          <View className='empty-state'>
            <Text className='empty-icon'>📚</Text>
            <Text className='empty-text'>还没有知识库</Text>
            <Text className='empty-hint'>点击右上角"新建"创建你的第一个知识库</Text>
          </View>
        ) : (
          bases.map((kb) => (
            <View key={kb.id} className='kb-card' onClick={() => handleGoDetail(kb)}>
              <View className='kb-card-header'>
                <Text className='kb-icon'>{kb.isSystem ? '🏛️' : '📚'}</Text>
                <View className='kb-info'>
                  <Text className='kb-name'>
                    {kb.name}
                    {kb.isSystem && <Text className='system-badge'>系统</Text>}
                  </Text>
                  <Text className='kb-desc'>{kb.description || '暂无描述'}</Text>
                </View>
              </View>
              <View className='kb-stats'>
                <Text className='stat-item'>📄 {kb.docCount} 份文档</Text>
                <Text className='stat-item'>🧩 {kb.chunkCount} 个分块</Text>
              </View>
              {!kb.isSystem && (
                <View className='kb-card-actions'>
                  <Text className='delete-btn' onClick={(e) => { e.stopPropagation(); handleDelete(kb) }}>
                    删除
                  </Text>
                </View>
              )}
            </View>
          ))
        )}
      </ScrollView>
    </View>
  )
}
