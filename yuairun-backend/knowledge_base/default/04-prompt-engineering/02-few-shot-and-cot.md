# Few-shot & Chain-of-Thought

## Few-shot Learning（少样本学习）

Few-shot 是指在 Prompt 中提供**少量输入输出示例**，帮助 LLM 理解期望的输出格式和质量。

## Few-shot 的类型

### 1. Zero-shot（零样本）

不给示例，只靠指令：

```
将以下句子翻译为英文："今天天气真好"
```

### 2. One-shot（单样本）

给一个示例：

```
将以下句子翻译为英文：
示例：昨天我去公园了 → Yesterday I went to the park.
现在请翻译：今天天气真好
```

### 3. Few-shot（少样本）

给多个示例，覆盖不同的变体：

```
将以下句子翻译为英文：

示例 1：昨天我去公园了 → Yesterday I went to the park.
示例 2：我在学习编程 → I am learning programming.
示例 3：这家餐厅的菜很好吃 → The food at this restaurant is delicious.

现在请翻译：今天天气真好
```

## Few-shot 的最佳实践

### 示例选择原则

1. **代表性**：示例要能代表你期望的输入分布
2. **多样性**：覆盖不同的输入变体
3. **质量高**：示例本身必须是高质量的
4. **数量适中**：3~5 个示例通常足够

### 在本项目中的应用

```python
# 出题 Prompt 中的 Few-shot 示例
FEW_SHOT_EXAMPLES = """
示例 1（单选题）：
题：TCP 建立连接时，客户端发送的第一个报文段的 SYN 标志位是？
A. SYN=0
B. SYN=1
C. SYN=2
D. SYN=3
答案：B
解析：TCP 三次握手中，客户端首先发送 SYN=1 的报文段...

示例 2（多选题）：
题：以下哪些是 TCP 拥塞控制算法？
A. 慢开始
B. 快恢复
C. 三次握手
D. 拥塞避免
答案：A、B、D
解析：TCP 拥塞控制包括慢开始、拥塞避免、快重传和快恢复...

示例 3（判断题）：
题：UDP 是面向连接的协议。
答案：错误
解析：UDP 是无连接协议，TCP 才是面向连接的。
"""
```

## Chain-of-Thought（链式思考）

Chain-of-Thought（CoT）引导 LLM **逐步推理**后再给出答案，能显著提升复杂推理任务的准确性。

### 基本的 CoT

```
❌ 不引导："计算 23 × 47 = ?"
→ 直接输出结果（可能算错）

✅ 引导："计算 23 × 47 = ? 请逐步计算"
→ 23 × 40 = 920
→ 23 × 7 = 161
→ 920 + 161 = 1081
→ 结果：1081
```

### CoT 的 Prompt 写法

```python
# 在 Prompt 中嵌入 CoT 指令
SYSTEM_PROMPT = """你是一位出题专家。在生成每道题之前，请先逐步推理：

1. 分析知识点：用户想考查什么概念？
2. 确定题型：单选/多选/判断？
3. 设计干扰项：每个错误选项应该对应什么常见误解？
4. 验证答案：确保正确答案无误。
5. 编写解析：解释为什么正确和为什么错误。

然后按以下 JSON 格式输出题目。"""
```

### Zero-shot CoT（零样本链式思考）

只需要在 Prompt 末尾加一句"让我们一步一步思考"：

```python
PROMPT = f"""
根据以下资料生成题目。

{topic}

让我们一步一步思考。
"""
```

### Few-shot CoT（少样本链式思考）

```python
FEW_SHOT_COT = """
示例：
问题：TCP 和 UDP 的区别是什么？

推理过程：
1. TCP 是面向连接的协议，UDP 是无连接协议
2. TCP 提供可靠传输，UDP 提供尽力而为的传输
3. TCP 有拥塞控制，UDP 没有
4. TCP 头部 20 字节，UDP 头部 8 字节

题目：
TCP 的头部最小长度是多少？
A. 8 字节
B. 20 字节
C. 40 字节
D. 60 字节
答案：B
"""
```

## CoT 的变体

### 1. Self-Consistency（自一致性）

多次运行相同 Prompt，取最一致的答案：

```python
# 多次采样
results = []
for _ in range(5):
    result = llm.invoke(prompt)
    results.append(result)

# 取出现最频繁的答案
final_answer = max(set(results), key=results.count)
```

### 2. Tree-of-Thought（思维树）

不仅逐步推理，还在每一步探索多个分支：

```
问题：设计一个登录系统

分支 1：使用 Session
├── 优点：简单
└── 缺点：不适用于移动端

分支 2：使用 JWT
├── 优点：无状态
└── 缺点：Token 过期处理

分支 3：使用 OAuth
├── 优点：第三方集成
└── 缺点：实现复杂
```

### 3. ReAct（推理+行动）

CoT 的 Agent 版本，推理过程中可以调用外部工具（详见 Agent 设计模式文档）。

## 使用场景对比

| 技术 | 适用场景 | 效果 |
|:----:|---------|:----:|
| Zero-shot | 简单任务 | ⭐⭐⭐ |
| Few-shot | 格式要求严格的输出 | ⭐⭐⭐⭐ |
| CoT | 数学、逻辑推理 | ⭐⭐⭐⭐⭐ |
| Self-Consistency | 需要高准确率 | ⭐⭐⭐⭐⭐ |
| Tree-of-Thought | 探索性、创造性任务 | ⭐⭐⭐⭐ |

## 最佳实践

1. **先 Zero-shot**：最简单的方案，效果不好再升级
2. **示例要精确**：Few-shot 示例的质量直接影响输出质量
3. **CoT 要引导**：告诉 LLM 从哪个角度开始思考
4. **注意 Token 消耗**：CoT 会增加输出长度
5. **结合结构化输出**：使用 with_structured_output 确保格式
