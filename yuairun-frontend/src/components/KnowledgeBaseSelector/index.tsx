/** 知识库选择器组件 */
import { View, Text } from '@tarojs/components'
import { useState, useEffect } from 'react'
import Taro from '@tarojs/taro'
import { getKnowledgeBases } from '../../services/knowledge'
import type { KnowledgeBase, SearchMode } from '../../types/knowledge'
import './index.scss'

interface Props {
  selectedKbId: string | null
  searchMode: SearchMode
  onSelectKb: (id: string | null, name: string | null) => void
  onSelectMode: (mode: SearchMode) => void
}

export default function KnowledgeBaseSelector({
  selectedKbId,
  searchMode,
  onSelectKb,
  onSelectMode,
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
    if (!selectedKbId) return '🌐 AI 搜索出题（默认）'
    const kb = bases.find((b) => b.id === selectedKbId)
    return kb ? `📚 ${kb.name}` : '🌐 AI 搜索出题（默认）'
  }

  const modeOptions: { value: SearchMode; label: string; icon: string; desc: string }[] = [
    { value: 'knowledge_base', label: '仅知识库', icon: '🔍', desc: '只从知识库检索' },
    { value: 'search', label: '仅 AI 搜索', icon: '🕸️', desc: '联网搜索最新资料' },
    { value: 'hybrid', label: '混合模式', icon: '🔀', desc: '知识库 + 联网搜索' },
  ]

  return (
    <View className='kb-selector'>
      {/* 选择器头部 */}
      <View className='kb-selector-header' onClick={() => setExpanded(!expanded)}>
        <View className='kb-selector-info'>
          <Text className='kb-current'>{getCurrentLabel()}</Text>
          <Text className='kb-arrow'>{expanded ? '▲' : '▼'}</Text>
        </View>
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
                  <Text className='kb-option-name'>AI 搜索出题</Text>
                  <Text className='kb-option-desc'>联网搜索最新资料出题</Text>
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

      {/* 选择了知识库后，显示搜索模式选择 */}
      {selectedKbId && (
        <View className='mode-selector'>
          <Text className='mode-label'>🎯 搜索模式</Text>
          <View className='mode-options'>
            {modeOptions.map((opt) => (
              <View
                key={opt.value}
                className={`mode-chip ${searchMode === opt.value ? 'active' : ''}`}
                onClick={() => onSelectMode(opt.value)}
              >
                <Text className='mode-icon'>{opt.icon}</Text>
                <Text className='mode-text'>{opt.label}</Text>
              </View>
            ))}
          </View>
          <Text className='mode-desc'>
            {modeOptions.find((m) => m.value === searchMode)?.desc}
          </Text>
        </View>
      )}
    </View>
  )
}
