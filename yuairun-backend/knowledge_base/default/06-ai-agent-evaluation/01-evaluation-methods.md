# AI Agent 评估方法

## 为什么需要评估 Agent？

AI Agent 的输出具有**不确定性和多样性**，传统的单元测试不足以保证质量。全面的评估体系是 Agent 从原型走向生产的关键。

## 评估维度

### 1. 任务完成率（Task Success Rate）

Agent 是否成功完成了用户的任务。

| 指标 | 定义 | 测量方式 |
|:----:|------|---------|
| **成功率** | 任务完全成功的比例 | 人工判断 / 自动验证 |
| **部分成功率** | 任务部分成功的比例 | 定义子任务完成度 |
| **失败率** | 完全失败的比例 | 异常日志统计 |

### 2. 效率指标（Efficiency）

| 指标 | 说明 | 目标值 |
|:----:|------|:------:|
| **平均耗时** | 从接收到完成的时间 | < 30s |
| **工具调用次数** | 平均每次任务的工具调用数 | < 8 次 |
| **Token 消耗** | 每次任务的总 token 数 | < 5000 tokens |
| **迭代次数** | 思考-行动循环的次数 | < 5 次 |

### 3. 质量指标（Quality）

| 指标 | 说明 | 评估方式 |
|:----:|------|---------|
| **准确性** | 回答是否事实正确 | 基于知识库验证 |
| **完整性** | 是否覆盖了所有需求 | 需求核对清单 |
| **相关性** | 回答是否紧扣问题 | 人工评分 |
| **可读性** | 语言是否清晰易懂 | 人工评分 |

### 4. 鲁棒性（Robustness）

| 测试场景 | 说明 |
|---------|------|
| **边界输入** | 空输入、超长输入、特殊字符 |
| **模糊指令** | "帮我处理一下"（需要澄清的指令） |
| **工具失败** | 搜索超时、API 不可用 |
| **多语言** | 中英混杂、中英混合输入 |

## 评估方法

### 1. 自动化评估

```python
class AgentEvaluator:
    """Agent 自动化评估"""
    
    def __init__(self, agent, test_cases: list[TestCase]):
        self.agent = agent
        self.test_cases = test_cases
    
    async def evaluate(self) -> EvaluationReport:
        results = []
        for case in self.test_cases:
            try:
                start = time.time()
                response = await self.agent.ainvoke({"input": case.input})
                elapsed = time.time() - start
                
                correctness = self.check_correctness(
                    response, case.expected_output
                )
                results.append({
                    "case": case.name,
                    "success": correctness,
                    "time": elapsed,
                    "tool_calls": self.count_tool_calls(response),
                })
            except Exception as e:
                results.append({
                    "case": case.name,
                    "success": False,
                    "error": str(e),
                })
        
        return EvaluationReport(results)
```

### 2. 基于 LLM 的评估（LLM-as-Judge）

使用另一个 LLM 来评估 Agent 的输出质量：

```python
EVALUATION_PROMPT = """
你是一个 AI Agent 评估专家。请评估以下 Agent 的回答质量。

用户问题：{question}
Agent 回答：{answer}
参考答案：{reference}

请从以下维度评分（1-5分）：
1. 准确性：回答是否事实正确？
2. 完整性：是否覆盖了所有要点？
3. 相关性：是否紧扣问题？
4. 清晰度：是否易于理解？

请输出 JSON 格式的评分结果。
"""
```

### 3. 人工评估

对于关键场景，人工评估仍然不可替代：

| 评估方式 | 适用场景 | 成本 |
|---------|---------|:----:|
| **A/B 测试** | 对比两个 Agent 版本 | 高 |
| **众包评估** | 大规模质量评估 | 中 |
| **专家评审** | 领域特定评估 | 高 |
| **用户满意度** | 线上真实用户反馈 | 低 |

## 评估测试集构建

### 测试用例类型

```python
test_cases = [
    # 1. 简单查询
    TestCase("简单查询", "什么是 TCP？", "传输控制协议..."),
    
    # 2. 复杂推理
    TestCase("复杂推理", "比较 TCP 和 UDP 的优缺点", "TCP: ... UDP: ..."),
    
    # 3. 多步操作
    TestCase("多步任务", "搜索最新的 AI Agent 框架并总结", "LangChain..."),
    
    # 4. 边界情况
    TestCase("空输入", "", "请输入内容"),
    TestCase("超长输入", "a" * 10000, "输入过长"),
    
    # 5. 错误恢复
    TestCase("工具超时", "搜索一个不存在的极端内容", "搜索失败，使用模型知识回答"),
]
```

## 持续评估流程

```
收集测试用例 → 运行评估 → 分析结果 → 改进 Agent → 重新评估
                                                      ↑
                                                      │
                            ──────────────────────────┘
```

### 评估报告示例

```json
{
  "version": "1.0.0",
  "timestamp": "2024-12-25T10:00:00Z",
  "summary": {
    "total_cases": 50,
    "passed": 42,
    "failed": 5,
    "errors": 3,
    "success_rate": 0.84
  },
  "metrics": {
    "avg_response_time": 12.5,
    "avg_tool_calls": 3.2,
    "avg_tokens": 2800
  },
  "failures": [
    {"case": "多语言混合输入", "error": "语言识别错误"},
    {"case": "工具超时", "error": "降级逻辑未触发"}
  ]
}
```

## 最佳实践

1. **从简单开始**：先用 10~20 个典型测试用例
2. **持续积累**：线上收集失败案例，补充到测试集
3. **多维度评估**：不要只看成功率，还要看效率和质量
4. **自动+人工结合**：自动跑基础测试，人工审核心场景
5. **版本对比**：每次修改后对比新旧版本的评估结果
6. **设置基线**：确定一个可接受的性能基线
