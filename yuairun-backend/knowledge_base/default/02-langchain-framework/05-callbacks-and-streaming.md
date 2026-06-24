# LangChain Callbacks & Streaming

## Callbacks（回调）

Callbacks 是 LangChain 的**事件监听系统**，它允许你在 Chain/Agent 执行的各个阶段插入自定义逻辑。

## 回调事件

完整的回调事件生命周期：

```
Chain 执行开始 (on_chain_start)
    │
    ├── LLM 调用开始 (on_llm_start)
    │   ├── LLM 生成新 token (on_llm_new_token)  ← 流式
    │   └── LLM 调用结束 (on_llm_end)
    │
    ├── Tool 调用开始 (on_tool_start)
    │   ├── Tool 执行
    │   └── Tool 调用结束 (on_tool_end)
    │
    └── Chain 执行结束 (on_chain_end)

异常情况:
    ├── on_llm_error
    ├── on_tool_error
    └── on_chain_error
```

### 常见回调事件

| 事件 | 时机 | 常用场景 |
|------|------|---------|
| `on_chain_start` | Chain 开始时 | 日志开始、计时开始 |
| `on_chain_end` | Chain 结束时 | 计时结束、记录结果 |
| `on_chain_error` | Chain 出错时 | 错误告警、降级处理 |
| `on_llm_start` | LLM 调用开始 | 记录请求 token |
| `on_llm_new_token` | LLM 生成新 token | **流式输出** |
| `on_llm_end` | LLM 调用结束 | 记录响应 token |
| `on_tool_start` | 工具调用开始 | 记录工具调用 |
| `on_tool_end` | 工具调用结束 | 记录工具结果 |
| `on_tool_error` | 工具调用失败 | 重试逻辑 |

## 实现自定义 Callback

### 方法 1：继承 BaseCallbackHandler

```python
from langchain_core.callbacks import BaseCallbackHandler

class LoggingCallbackHandler(BaseCallbackHandler):
    """自定义回调处理器"""
    
    def on_llm_start(self, serialized, prompts, **kwargs):
        print(f"LLM 调用开始: {prompts}")
    
    def on_llm_end(self, response, **kwargs):
        print(f"LLM 调用结束: {response.generations[0][0].text[:50]}...")
    
    def on_tool_start(self, serialized, input_str, **kwargs):
        print(f"工具调用: {serialized['name']}, 输入: {input_str}")
    
    def on_tool_end(self, output, **kwargs):
        print(f"工具结果: {str(output)[:100]}...")
    
    def on_chain_error(self, error, **kwargs):
        print(f"Chain 执行失败: {error}")
```

### 方法 2：使用 `@callback` 装饰器

```python
from langchain_core.callbacks import callback_manager

@callback_manager
def my_function():
    pass
```

## 使用 Callback

```python
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

handler = LoggingCallbackHandler()

# 方式 1：全局配置
chain = prompt | ChatOpenAI(callbacks=[handler]) | parser

# 方式 2：运行时传入
chain.invoke({"input": "你好"}, config={"callbacks": [handler]})

# 方式 3：使用 callback_manager 上下文
from langchain_core.callbacks import CallbackManager

manager = CallbackManager([handler])
chain.invoke({"input": "你好"}, config={"callbacks": manager})
```

## Streaming（流式输出）

流式输出让 AI 的响应能够**逐字显示**，而不是等全部生成完再一次性展示，大幅提升用户体验。

### 基本流式

```python
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(streaming=True)  # 启用流式

for chunk in chain.stream({"input": "讲个故事"}):
    print(chunk.content, end="", flush=True)
```

### 在 FastAPI 中使用 SSE 流式

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from langchain_openai import ChatOpenAI

app = FastAPI()

async def generate_stream(topic: str):
    chain = prompt | ChatOpenAI(streaming=True) | StrOutputParser()
    async for chunk in chain.astream({"topic": topic}):
        yield f"data: {chunk}\n\n"  # SSE 格式

@app.post("/api/stream")
async def stream_endpoint(topic: str):
    return StreamingResponse(
        generate_stream(topic),
        media_type="text/event-stream",
    )
```

### 前端接收流式

```javascript
// 使用 EventSource 或 fetch
const response = await fetch("/api/stream", {
    method: "POST",
    body: JSON.stringify({ topic: "TCP" }),
});

const reader = response.body.getReader();
while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    // 逐块处理
    const text = new TextDecoder().decode(value);
    // 更新 UI
}
```

## Agent 的流式输出

Agent 的流式比普通 Chain 复杂，因为需要展示 Agent 的**思考和工具调用过程**：

```python
from langchain.agents import AgentExecutor

# Agent 的流式输出包含思考过程和工具调用
async for chunk in agent_executor.astream({"input": "搜索互联网..."}):
    if "actions" in chunk:  # Agent 正在调用工具
        print(f"🛠️ 调用工具: {chunk['actions'][0].tool}")
    elif "steps" in chunk:  # 工具返回结果
        print(f"📥 获取结果")
    elif "output" in chunk:  # 最终输出
        print(f"✅ {chunk['output']}")
```

## 实际应用

### 日志记录

```python
class LogCallback(BaseCallbackHandler):
    def on_llm_start(self, serialized, prompts, **kwargs):
        logger.info(f"[LLM] 请求: {prompts}")
    
    def on_llm_end(self, response, **kwargs):
        token_usage = response.llm_output.get("token_usage", {})
        logger.info(f"[LLM] Token 使用: {token_usage}")
```

### 速率限制

```python
class RateLimitCallback(BaseCallbackHandler):
    def __init__(self, max_calls_per_minute=60):
        self.max_calls = max_calls_per_minute
        self.call_times = []
    
    def on_llm_start(self, **kwargs):
        now = time.time()
        self.call_times = [t for t in self.call_times if now - t < 60]
        if len(self.call_times) >= self.max_calls:
            raise Exception("速率限制")
        self.call_times.append(now)
```
