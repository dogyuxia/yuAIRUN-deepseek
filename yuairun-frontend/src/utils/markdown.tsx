/** 简易 Markdown 解析器 - 将分析报告文本转为格式化组件 */
import { View, Text } from '@tarojs/components'

// 注意：内联样式中的 px 不会被 Taro 转成 rpx，所以值需要约 SCSS 的一半
// SCSS 中 26px → 26rpx → 约 13px 物理像素
// 内联样式直接用 13px 才能匹配

/** 解析行内样式（粗体等） */
function parseInline(text: string): JSX.Element[] {
  if (!text) return [<Text key="empty"> </Text>]
  const parts = text.split(/(\*\*[^*]+\*\*)/g)
  return parts.filter(Boolean).map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return <Text key={i} style={{ fontWeight: 700, color: '#3D2C2E' }}>{part.slice(2, -2)}</Text>
    }
    return <Text key={i}>{part}</Text>
  })
}

/** 将分析报告文本解析为格式化节点 */
export function renderAnalysisText(text: string): JSX.Element {
  if (!text) return <View />

  const lines = text.split('\n')
  const elements: JSX.Element[] = []
  let listItems: JSX.Element[] = []
  let listIdx = 0

  function flushList() {
    if (listItems.length > 0) {
      elements.push(
        <View key={`list_${listIdx++}`} style={{ paddingLeft: '20px', marginBottom: '6px' }}>
          {listItems}
        </View>
      )
      listItems = []
    }
  }

  lines.forEach((line, i) => {
    const trimmed = line.trim()
    if (!trimmed) return

    // 分隔线
    if (/^[-=]{3,}$/.test(trimmed)) {
      flushList()
      elements.push(
        <View key={`hr${i}`} style={{ height: '1px', background: '#EDE4DE', margin: '10px 0' }} />
      )
      return
    }

    // 标题: # 或 ## 或 ### 或 ▎
    const headingMatch = trimmed.match(/^(#{1,3}|▎)\s+(.+)/)
    if (headingMatch) {
      flushList()
      const isMajor = headingMatch[1] === '#'
      elements.push(
        <Text key={`h${i}`} style={{
          display: 'block',
          fontSize: isMajor ? '16px' : '14px',
          fontWeight: 700,
          color: isMajor ? '#3D2C2E' : '#C97B6B',
          marginBottom: '6px',
          marginTop: '4px',
          lineHeight: 1.5,
        }}>
          {parseInline(headingMatch[2])}
        </Text>
      )
      return
    }

    // 引用: > xxx
    const quoteMatch = trimmed.match(/^>\s+(.+)/)
    if (quoteMatch) {
      flushList()
      elements.push(
        <View key={`q${i}`} style={{
          padding: '8px 12px',
          background: '#F5EDE8',
          borderRadius: '10px',
          marginBottom: '8px',
          borderLeft: '3px solid #C97B6B',
        }}>
          <Text style={{ fontSize: '13px', color: '#A0887E', fontStyle: 'italic', lineHeight: 1.6 }}>
            {parseInline(quoteMatch[1])}
          </Text>
        </View>
      )
      return
    }

    // 列表项: - / · / * / + / 1. 开头
    const listMatch = trimmed.match(/^([-·*+\d]+\.?)\s+(.+)/)
    if (listMatch) {
      const content = listMatch[2]
      listItems.push(
        <Text key={`li${i}`} style={{
          display: 'block',
          fontSize: '13px',
          lineHeight: 1.8,
          color: '#5A4547',
        }}>
          <Text style={{ color: '#C97B6B', marginRight: '6px' }}>•</Text>
          {parseInline(content)}
        </Text>
      )
      return
    }

    // 普通段落
    flushList()
    elements.push(
      <Text key={`p${i}`} style={{
        display: 'block',
        fontSize: '13px',
        lineHeight: 1.8,
        color: '#5A4547',
        marginBottom: '4px',
      }}>
        {parseInline(trimmed)}
      </Text>
    )
  })

  flushList()
  return <View>{elements}</View>
}
