"""出题 LangChain 链定义"""

import json
import logging
import re

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import create_agent
from langchain_tavily import TavilySearch, TavilyExtract

from app.config import get_settings
from app.models.quiz import QuizResponse
from app.prompts.quiz_prompt import (
    QUIZ_SYSTEM_PROMPT,
    QUIZ_HUMAN_PROMPT,
    SEARCH_QUIZ_SYSTEM_PROMPT,
    SEARCH_QUIZ_HUMAN_PROMPT,
)
from app.utils.mock_llm import get_mock_quiz_response

logger = logging.getLogger(__name__)


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


def create_search_augmented_quiz_chain():
    """
    创建搜索增强出题链（Agent 驱动）

    将 TavilySearch 和 TavilyExtract 工具提供给 AI Agent，
    AI 自主决定搜索策略，基于搜索结果生成题目。

    Returns:
        SearchAugmentedQuizChain 实例
    """
    settings = get_settings()

    # 设置 Tavily API Key
    import os
    if settings.tavily_api_key:
        os.environ["TAVILY_API_KEY"] = settings.tavily_api_key

    # 创建 LLM
    llm = ChatOpenAI(
        model="deepseek-chat",
        openai_api_key=settings.deepseek_api_key,
        openai_api_base=settings.deepseek_base_url,
        temperature=0.7,
        timeout=120,  # Agent 模式需要更长的超时时间
        max_retries=2,
    )

    return SearchAugmentedQuizChain(llm)


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


class SearchAugmentedQuizChain:
    """搜索增强出题链 - Agent 驱动

    AI Agent 拥有 TavilySearch 和 TavilyExtract 两个工具，
    可以自主决定：
    - 用户输入 URL → 调用 TavilyExtract 提取页面内容
    - 用户输入关键词 → 调用 TavilySearch 搜索最新资料
    - 动态调整 search_depth、max_results、time_range 等参数
    - 搜索失败时降级使用自身知识
    """

    def __init__(self, llm):
        self.llm = llm

    async def ainvoke(self, inputs: dict) -> QuizResponse:
        """异步执行搜索增强出题"""
        try:
            # 创建 Tavily 工具
            tavily_search = TavilySearch(
                max_results=5,
                topic="general",
            )
            tavily_extract = TavilyExtract()

            # 创建 Agent
            agent = create_agent(
                model=self.llm,
                tools=[tavily_search, tavily_extract],
                system_prompt=SEARCH_QUIZ_SYSTEM_PROMPT,
            )

            # 构建 Human Prompt
            human_prompt = SEARCH_QUIZ_HUMAN_PROMPT.format(**inputs)

            # 调用 Agent（搜索 → 收集资料 → 出题）
            result = await agent.ainvoke({
                "messages": [{"role": "user", "content": human_prompt}]
            })

            # 从最终消息中提取 JSON
            final_message = result["messages"][-1]
            content = final_message.content if hasattr(final_message, 'content') else str(final_message)
            parsed = parse_json_response(content)
            return QuizResponse(**parsed)

        except Exception as e:
            logger.warning("Search-augmented quiz generation failed, falling back to traditional chain: %s", str(e))
            # 降级：使用传统出题链
            fallback_chain = QuizChain(
                self.llm,
                ChatPromptTemplate.from_messages([
                    ("system", QUIZ_SYSTEM_PROMPT),
                    ("human", QUIZ_HUMAN_PROMPT),
                ]),
            )
            return await fallback_chain.ainvoke(inputs)

    def invoke(self, inputs: dict) -> QuizResponse:
        """同步执行搜索增强出题"""
        import asyncio
        return asyncio.run(self.ainvoke(inputs))


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
