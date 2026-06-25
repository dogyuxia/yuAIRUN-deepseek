/** 知识库详情页 — 文档列表 + 上传入口 */
import { View, Text, Button, ScrollView, Image } from '@tarojs/components'
import Taro from '@tarojs/taro'
import { useState, useEffect } from 'react'
import { getKbDocuments, uploadDocument, deleteDocument } from '../../services/knowledge'
import type { KnowledgeDocument } from '../../types/knowledge'
import './index.scss'

export default function KnowledgeDetailPage() {
  const params = Taro.getCurrentInstance().router?.params || {}
  const kbId = params.kbId as string || ''
  const kbName = params.name ? decodeURIComponent(params.name as string) : '知识库'

  const [docs, setDocs] = useState<KnowledgeDocument[]>([])
  const [loading, setLoading] = useState(true)
  const [uploading, setUploading] = useState(false)

  useEffect(() => {
    loadDocuments()
  }, [])

  const loadDocuments = async () => {
    setLoading(true)
    try {
      const res = await getKbDocuments(kbId)
      if (res.success) {
        setDocs(res.data)
      }
    } catch (e) {
      console.error('加载文档失败', e)
    } finally {
      setLoading(false)
    }
  }

  const handleUpload = async () => {
    try {
      const res = await Taro.chooseMessageFile({
        count: 1,
        type: 'file',
        extension: ['pdf', 'docx', 'txt', 'md'],
      })

      if (res.tempFiles && res.tempFiles.length > 0) {
        const file = res.tempFiles[0]
        const maxSize = 20 * 1024 * 1024 // 20MB

        if (file.size > maxSize) {
          Taro.showToast({ title: '文件大小不能超过 20MB', icon: 'none' })
          return
        }

        setUploading(true)
        const result = await uploadDocument(kbId, file.path, file.name || file.path)
        if (result.success) {
          Taro.showToast({ title: '上传成功，正在处理', icon: 'success' })
          loadDocuments()
        } else {
          Taro.showToast({ title: result.error || '上传失败', icon: 'none' })
        }
      }
    } catch (e) {
      console.error('选择文件失败', e)
      Taro.showToast({ title: '请从聊天中选择文件上传', icon: 'none' })
    } finally {
      setUploading(false)
    }
  }

  const handleDeleteDoc = (doc: KnowledgeDocument) => {
    Taro.showModal({
      title: '删除文档',
      content: `确定要删除"${doc.filename}"吗？`,
      success: async (res) => {
        if (res.confirm) {
          const result = await deleteDocument(doc.id)
          if (result.success) {
            Taro.showToast({ title: '已删除', icon: 'success' })
            loadDocuments()
          } else {
            Taro.showToast({ title: result.error || '删除失败', icon: 'none' })
          }
        }
      },
    })
  }

  const getStatusTag = (status: string) => {
    const map: Record<string, { text: string; className: string }> = {
      pending: { text: '等待处理', className: 'tag-pending' },
      processing: { text: '处理中', className: 'tag-processing' },
      ready: { text: '已就绪', className: 'tag-ready' },
      failed: { text: '处理失败', className: 'tag-failed' },
    }
    return map[status] || { text: status, className: 'tag-pending' }
  }

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes}B`
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)}KB`
    return `${(bytes / (1024 * 1024)).toFixed(1)}MB`
  }

  const getFileIcon = (type: string) => {
    const icons: Record<string, string> = {
      pdf: '📕', docx: '📘', txt: '📄', md: '📝',
    }
    return icons[type] || '📄'
  }

  return (
    <View className='kb-detail-page'>
      <View className='gradient-bar' />

      {/* 导航 */}
      <View className='detail-nav'>
        <View className='nav-back' onClick={() => Taro.navigateBack()}>← 返回</View>
        <Text className='nav-title'>{kbName}</Text>
        <View className='nav-spacer' />
      </View>

      {/* 上传入口 */}
      <View className='upload-section'>
        <Button className='upload-btn' onClick={handleUpload} loading={uploading} disabled={uploading}>
          📤 上传文档
        </Button>
        <Text className='upload-hint'>支持 PDF、DOCX、TXT、Markdown，单文件 ≤ 20MB</Text>
      </View>

      {/* 文档列表 */}
      <ScrollView className='doc-list' scrollY>
        <Text className='section-title'>文档列表 ({docs.length})</Text>

        {loading ? (
          <View className='loading-state'>
            {[1, 2].map((i) => <View key={i} className='skeleton-doc' />)}
          </View>
        ) : docs.length === 0 ? (
          <View className='empty-docs'>
            <Text className='empty-icon'>📂</Text>
            <Text className='empty-text'>还没有文档</Text>
            <Text className='empty-hint'>点击上方按钮上传文档</Text>
          </View>
        ) : (
          docs.map((doc) => {
            const statusTag = getStatusTag(doc.status)
            return (
              <View key={doc.id} className='doc-card'>
                <View className='doc-icon'>{getFileIcon(doc.fileType)}</View>
                <View className='doc-info'>
                  <Text className='doc-name'>{doc.filename}</Text>
                  <View className='doc-meta'>
                    <Text className='doc-size'>{formatSize(doc.fileSize)}</Text>
                    {doc.chunkCount > 0 && <Text className='doc-chunks'>{doc.chunkCount} 块</Text>}
                    <Text className={`doc-status ${statusTag.className}`}>{statusTag.text}</Text>
                  </View>
                </View>
                {doc.status !== 'processing' && (
                  <Text className='doc-delete' onClick={() => handleDeleteDoc(doc)}>✕</Text>
                )}
              </View>
            )
          })
        )}
      </ScrollView>
    </View>
  )
}
