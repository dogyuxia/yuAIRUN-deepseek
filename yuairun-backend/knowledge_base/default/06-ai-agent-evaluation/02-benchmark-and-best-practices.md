# Benchmark 与最佳实践

## AI Agent 的 Benchmark

Benchmark（基准测试）是衡量 AI Agent 性能的标准测试集。以下是一些主流的 AI Agent Benchmark。

## 主流 Benchmark

### 1. GAIA

**全称**：General AI Assistants
**发布方**：Meta FAIR、Hugging Face
**评估内容**：通用 AI 助手能力

| 维度 | 说明 |
|:----:|------|
| **类型** | 问答、多步推理、工具使用 |
| **题量** | 466 道 |
| **难度** | 分为三个等级 |
| **开放性** | 需要搜索、推理、工具调用 |

### 2. SWE-bench

**全称**：Software Engineering Benchmark
**发布方**：Princeton University
**评估内容**：AI 代码修复能力

| 维度 | 说明 |
|:----:|------|
| **任务** | 修复真实 GitHub Issue |
| **题量** | 2294 个 GitHub Issue |
| **评估方式** | 生成的 patch 是否能通过测试 |
| **代表性项目** | Django、Flask、SymPy 等 |

### 3. ToolBench

**发布方**：清华大学
**评估内容**：Agent 的工具使用能力

| 维度 | 说明 |
|:----:|------|
| **工具集** | 50+ 真实 API |
| **任务** | 多步骤工具调用任务 |
| **评估维度** | 工具选择、参数匹配、结果处理 |

### 4. AgentBench

**发布方**：清华大学、Ohio State 等
**评估内容**：多维度 Agent 能力

| 维度 | 说明 |
|:----:|------|
| **测试集** | 8 个不同环境 |
| **能力** | 推理、规划、工具使用 |
| **环境** | 操作系统、数据库、Web 等 |

## Agent 开发的最佳实践

### 1. Tool 设计

| 原则 | 说明 |
|:----:|------|
| **单一职责** | 一个工具只做一件事 |
| **清晰命名** | `web_search` 比 `tool1` 好 |
| **详细描述** | 描述何时使用、参数含义 |
| **容错设计** | 返回友好错误信息，不要抛出异常 |

### 2. Prompt 设计

| 原则 | 说明 |
|:----:|------|
| **角色明确** | 告诉 Agent 它是谁、要做什么 |
| **分步引导** | 给出思考框架，不要只给最终目标 |
| **工具说明** | 列出每个工具的用途和调用时机 |
| **输出格式** | 明确指定输出格式和字段含义 |

### 3. 错误处理

```python
# 层级降级策略
try:
    # Level 1：正常执行
    result = await agent.ainvoke(input)
except ToolException:
    # Level 2：工具失败，用备用工具
    result = await agent.ainvoke_with_fallback(input)
except TimeoutError:
    # Level 3：超时，只用模型知识
    result = await model_only_chain.ainvoke(input)
except Exception:
    # Level 4：完全失败，返回友好提示
    result = {"error": "暂时无法处理，请稍后重试"}
```

### 4. 可观测性

```python
class AgentMonitor:
    """Agent 监控"""
    
    def log_step(self, agent_id, step_type, input_data, output_data, duration):
        """记录每一步的详细信息"""
        self.logs.append({
            "agent_id": agent_id,
            "step_type": step_type,  # thought / action / observation
            "input": input_data,
            "output": output_data,
            "duration_ms": duration * 1000,
            "timestamp": time.time(),
        })
    
    def get_metrics(self):
        """生成性能指标"""
        return {
            "total_steps": len(self.logs),
            "total_duration": sum(l["duration_ms"] for l in self.logs),
            "tool_calls": sum(1 for l in self.logs if l["step_type"] == "action"),
            "failures": sum(1 for l in self.logs if "error" in l["output"]),
        }
```

### 5. 安全考虑

| 安全措施 | 说明 |
|---------|------|
| **工具白名单** | 只允许调用预定义的工具 |
| **操作确认** | 删除/修改等危险操作需用户确认 |
| **速率限制** | 控制调用频率，防止滥用 |
| **输入过滤** | 过滤 Prompt 注入攻击 |
| **审计日志** | 记录所有 Agent 操作 |

### 6. 成本控制

```python
class CostController:
    """Agent 成本控制"""
    
    MAX_COST_PER_TASK = 0.05  # 每次任务最大成本（美元）
    
    def check_budget(self, task):
        # 预估成本
        estimated_cost = self.estimate_cost(task)
        if estimated_cost > self.MAX_COST_PER_TASK:
            # 简化策略
            return self.create_lightweight_plan(task)
        return task
```

## 常见陷阱

| 陷阱 | 表现 | 解决方案 |
|:----:|------|---------|
| **无限循环** | Agent 反复调用同一个工具 | 设置 max_iterations |
| **工具误选** | 用搜索工具算数学 | 改进工具描述 |
| **上下文溢出** | token 超限 | 使用摘要压缩 |
| **过度依赖工具** | 简单问题也调用工具 | 允许"不调用工具"的选项 |
| **幻觉传播** | 一次错误导致后续全错 | 增加验证节点 |

## 生产环境 Checklist

- [ ] 设置 `max_iterations` 防止无限循环
- [ ] 所有工具有超时设置
- [ ] 工具调用有重试和降级机制
- [ ] 记录完整的 Agent 执行日志
- [ ] 设置 token 消耗上限
- [ ] 敏感操作需人工确认
- [ ] 定期运行评估测试集
- [ ] 监控成功率、延迟、成本
- [ ] 有优雅的降级方案
- [ ] A/B 测试新版本再上线
