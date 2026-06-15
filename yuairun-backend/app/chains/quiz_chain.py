"""出题 LangChain 链定义"""

import json
import re

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from app.config import get_settings
from app.models.quiz import QuizResponse
from app.prompts.quiz_prompt import QUIZ_SYSTEM_PROMPT, QUIZ_HUMAN_PROMPT
from app.utils.mock_llm import get_mock_quiz_response


def parse_json_response(text: str) -> dict:
    """从 LLM 响应中提取并解析 JSON"""
    # 尝试提取 ```json ... ``` 代码块
    match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if match:
        text = match.group(1).strip()
    # 尝试找到第一个 { 到最后一个 }
    start = text.find('{')
    end = text.rfind('}')
    if start >= 0 and end > start:
        text = text[start:end + 1]
    return json.loads(text)


def create_quiz_chain(use_mock: bool = False):
    """
    创建出题 LangChain 链

    Args:
        use_mock: 是否使用 Mock LLM（测试用）

    Returns:
        可调用的链对象
    """
    settings = get_settings()

    if use_mock:
        return MockQuizChain()

    llm = ChatOpenAI(
        model="deepseek-chat",
        openai_api_key=settings.deepseek_api_key,
        openai_api_base=settings.deepseek_base_url,
        temperature=0.7,
        timeout=90,
        max_retries=2,
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", QUIZ_SYSTEM_PROMPT),
        ("human", QUIZ_HUMAN_PROMPT),
    ])

    return QuizChain(llm, prompt)


class QuizChain:
    """出题链 - 通过 Prompt 引导 LLM 输出 JSON，手动解析"""

    def __init__(self, llm, prompt):
        self.llm = llm
        self.prompt = prompt

    async def ainvoke(self, inputs: dict) -> QuizResponse:
        chain = self.prompt | self.llm
        result = await chain.ainvoke(inputs)
        parsed = parse_json_response(result.content)
        return QuizResponse(**parsed)

    def invoke(self, inputs: dict) -> QuizResponse:
        chain = self.prompt | self.llm
        result = chain.invoke(inputs)
        parsed = parse_json_response(result.content)
        return QuizResponse(**parsed)


class MockQuizChain:
    """Mock 出题链，用于开发测试"""

    async def ainvoke(self, inputs: dict) -> QuizResponse:
        """模拟异步调用"""
        import asyncio
        await asyncio.sleep(1)  # 模拟网络延迟

        result = get_mock_quiz_response(
            subject=inputs.get("subject", ""),
            topic=inputs.get("topic", ""),
            count=inputs.get("count", 5),
        )
        return QuizResponse(**result)

    def invoke(self, inputs: dict) -> QuizResponse:
        """模拟同步调用"""
        result = get_mock_quiz_response(
            subject=inputs.get("subject", ""),
            topic=inputs.get("topic", ""),
            count=inputs.get("count", 5),
        )
        return QuizResponse(**result)
