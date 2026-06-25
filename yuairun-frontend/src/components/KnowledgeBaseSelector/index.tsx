/** 知识库选择器组件 — 仅选择知识库，AI 自主决定检索方式 */
import { View, Text } from '@tarojs/components'
import { useState, useEffect } from 'react'
import Taro from '@tarojs/taro'
import { getKnowledgeBases } from '../../services/knowledge'
import type { KnowledgeBase } from '../../types/knowledge'
import './index.scss'

interface Props {
  selectedKbId: string | null
  onSelectKb: (id: string | null, name: string | null) => void
}

export default function KnowledgeBaseSelector({
  selectedKbId,
  onSelectKb,
}: Props) {
  const [bases, setBases] = useState<KnowledgeBase[]>([])
  const [expanded, setExpanded] = useState(false)
  const [loading, setLoading] = useState(false)
  const [loadError, setLoadError] = useState<string | null>(null)

  useEffect(() => {
    loadBases()
  }, [])

  const loadBases = async () => {
    setLoading(true)
    setLoadError(null)
    try {
      const res = await getKnowledgeBases()
      if (res.success) {
        setBases(res.data || [])
        if (!res.data || res.data.length === 0) {
          setLoadError('暂无可用知识库，请在"管理知识库"中创建')
        }
      } else {
        setLoadError(res.error || '加载知识库失败')
      }
    } catch (e) {
      setLoadError('网络异常，无法加载知识库')
    } finally {
      setLoading(false)
    }
  }

  const handleSelect = (kb: KnowledgeBase | null) => {
    if (kb) {
      onSelectKb(kb.id, kb.name)
    } else {
      onSelectKb(null, null)
    }
    setExpanded(false)
  }

  const getCurrentLabel = () => {
    if (!selectedKbId) return '🌐 AI 智能出题（默认）'
    const kb = bases.find((b) => b.id === selectedKbId)
    return kb ? `📚 ${kb.name}` : '🌐 AI 智能出题（默认）'
  }

  return (
    <View className='kb-selector'>
      {/* 选择器头部 */}
      <View className='kb-selector-header' onClick={() => setExpanded(!expanded)}>
        <View className='kb-selector-info'>
          <Text className='kb-current'>{getCurrentLabel()}</Text>
          <Text className='kb-arrow'>{expanded ? '▲' : '▼'}</Text>
        </View>
        {selectedKbId && (
          <View className='kb-autobadge'>🤖 AI 自动决策</View>
        )}
      </View>

      {/* 展开后的列表 */}
      {expanded && (
        <View className='kb-selector-body'>
          {loading ? (
            <View className='kb-loading'>加载中...</View>
          ) : loadError ? (
            <View className='kb-error'>
              <Text className='kb-error-text'>{loadError}</Text>
              <Text className='kb-retry-btn' onClick={() => loadBases()}>点击重试</Text>
            </View>
          ) : (
            <>
              {/* 默认选项 */}
              <View
                className={`kb-option ${!selectedKbId ? 'active' : ''}`}
                onClick={() => handleSelect(null)}
              >
                <Text className='kb-option-icon'>🌐</Text>
                <View className='kb-option-info'>
                  <Text className='kb-option-name'>AI 智能出题</Text>
                  <Text className='kb-option-desc'>AI 会自动联网搜索最新资料出题</Text>
                </View>
              </View>

              {/* 知识库列表 */}
              {bases.map((kb) => (
                <View
                  key={kb.id}
                  className={`kb-option ${selectedKbId === kb.id ? 'active' : ''}`}
                  onClick={() => handleSelect(kb)}
                >
                  <Text className='kb-option-icon'>{kb.isSystem ? '🏛️' : '📚'}</Text>
                  <View className='kb-option-info'>
                    <View className='kb-option-name-row'>
                      <Text className='kb-option-name'>{kb.name}</Text>
                      {kb.isSystem && <Text className='kb-badge'>系统</Text>}
                    </View>
                    <Text className='kb-option-desc'>{kb.docCount} 份文档 · {kb.chunkCount} 个分块</Text>
                  </View>
                </View>
              ))}
            </>
          )}
        </View>
      )}
    </View>
  )
}
