# AI 与大模型面试题

## 1. Transformer 核心组件

**Self-Attention 计算流程：**
1. 输入 X 分别乘 Wq、Wk、Wv 得到 Q、K、V
2. 计算注意力分数：`Attention(Q,K,V) = softmax(QK^T / √d) · V`
3. 除以 √d 防止梯度消失

**Multi-Head Attention：** 将 Q、K、V 拆成多个头分别计算，再拼接融合，捕捉不同子空间的信息。

**位置编码：** 由于 Self-Attention 不具备位置感知能力，需要加入位置编码（正弦波或可学习参数）。

## 2. LLM 推理优化

| 技术 | 原理 | 效果 |
|:----|------|:----:|
| **KV Cache** | 缓存已计算的 K、V 矩阵 | 避免重复计算，加速自回归生成 |
| **GQA** | 分组查询注意力，多个 Q 头共享 K、V | 减少显存占用 |
| **Flash Attention** | 分块计算 + 软合并 | 减少显存读写，IO 优化 |
| **Quantization** | INT4/INT8 量化权重 | 模型体积缩小 4x |
| **Speculative Decoding** | 小模型先预测，大模型验证 | 加速 2~3x |

## 3. RAG 技术要点

**RAG 流程：** 用户 Query → Embedding → 向量检索 → 检索结果 + Query 组装 Prompt → LLM 生成回答

**Chunking 策略：**
- 固定长度分块（chunk_size=500, overlap=100）
- 语义分块（按段落、标题层级切割）
- 考虑检索任务调整块大小

**检索优化：**
- 混合检索：向量相似度 + BM25 关键词
- 重排序：粗排（向量）→ 精排（cross-encoder）
- HyDE：让 LLM 生成假设文档后再检索

## 4. 微调方法对比

| 方法 | 参数量 | 原理 | 适用场景 |
|:----|:-----:|------|---------|
| Full Fine-tuning | 100% | 更新全部参数 | 有充足 GPU 资源 |
| LoRA | 0.1~1% | 低秩适配矩阵 | 快速适配小任务 |
| QLoRA | 0.05% | 4bit 量化 + LoRA | 单卡即可微调 |
| P-Tuning v2 | 0.1% | 连续提示向量 | NLU 任务 |

## 5. Agent 设计模式

**ReAct 模式（思考+行动循环）：**
1. Thought：分析当前状态和目标
2. Action：选择一个工具执行
3. Observation：观察工具返回结果
4. 重复上述步骤直到完成任务

**Tool-use 设计要点：**
- 工具描述要清晰，让 LLM 知道何时使用
- 参数定义规范，用 JSON Schema
- 错误处理：工具失败后的重试和降级策略
