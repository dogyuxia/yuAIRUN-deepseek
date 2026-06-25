"""出题 LangChain 链定义"""

import json
import logging

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
    AGENTIC_QUIZ_SYSTEM_PROMPT,
    AGENTIC_QUIZ_HUMAN_PROMPT,
)
from app.utils.mock_llm import get_mock_quiz_response

logger = logging.getLogger(__name__)


# ============================================================
# JSON 解析工具 — DeepSeek 不支持 with_structured_output，
# 因此所有链统一使用 Prompt 引导 JSON 输出 + 手动解析
# ============================================================

def parse_json_response(text: str) -> dict:
    """
    从 LLM 响应中提取并解析 JSON。

    DeepSeek API 不支持 OpenAI 的 response_format/with_structured_output，
    因此所有 LLM 调用都通过 Prompt 要求输出 JSON，再手动解析。
    """
    match = __import__('re').search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if match:
        text = match.group(1).strip()
    start = text.find('{')
    end = text.rfind('}')
    if start >= 0 and end > start:
        text = text[start:end + 1]
    return json.loads(text)


def safe_parse_json(text: str) -> dict | None:
    """
    安全解析 JSON，失败时返回 None 而不是抛异常。
    """
    try:
        return parse_json_response(text)
    except (json.JSONDecodeError, ValueError, Exception) as e:
        logger.warning("JSON 解析失败: %s | 前100字符: %s", e, text[:100])
        return None


# ============================================================
# 创建 LLM 实例
# ============================================================

def _create_llm(timeout: int = 90):
    """创建 DeepSeek ChatOpenAI 实例"""
    settings = get_settings()
    return ChatOpenAI(
        model="deepseek-chat",
        openai_api_key=settings.deepseek_api_key,
        openai_api_base=settings.deepseek_base_url,
        temperature=0.7,
        timeout=timeout,
        max_retries=2,
    )


# ============================================================
# 工厂函数
# ============================================================

def create_quiz_chain(use_mock: bool = False):
    """
    创建出题 LangChain 链（通过 Prompt 引导 JSON 输出 + 手动解析）

    Args:
        use_mock: 是否使用 Mock LLM（测试用）

    Returns:
        可调用的链对象
    """
    if use_mock:
        return MockQuizChain()

    llm = _create_llm(timeout=90)
    prompt = ChatPromptTemplate.from_messages([
        ("system", QUIZ_SYSTEM_PROMPT),
        ("human", QUIZ_HUMAN_PROMPT),
    ])

    return QuizChain(llm, prompt)


def create_agentic_quiz_chain(
    knowledge_base_id: str | None = None,
    knowledge_base_name: str = "",
):
    """
    创建 Agentic RAG 出题链

    AI Agent 自主分析用户 topic 并决定检索策略：
    - 有知识库时优先检索知识库，不充分则补充联网搜索
    - 无知识库时直接联网搜索

    Args:
        knowledge_base_id: 知识库 ID（可选）
        knowledge_base_name: 知识库名称（可选）

    Returns:
        AgenticQuizChain 实例
    """
    from app.chains.agentic_quiz_chain import AgenticQuizChain
    return AgenticQuizChain(
        knowledge_base_id=knowledge_base_id,
        knowledge_base_name=knowledge_base_name,
    )


def create_search_augmented_quiz_chain():
    """
    创建搜索增强出题链（Agent 驱动）

    将 TavilySearch 和 TavilyExtract 工具提供给 AI Agent，
    AI 自主决定搜索策略，基于搜索结果生成题目。

    Returns:
        SearchAugmentedQuizChain 实例
    """
    settings = get_settings()

    import os
    if settings.tavily_api_key:
        os.environ["TAVILY_API_KEY"] = settings.tavily_api_key

    llm = _create_llm(timeout=120)
    return SearchAugmentedQuizChain(llm)


# ============================================================
# QuizChain — Prompt 引导 JSON 输出 + 手动解析
# ============================================================

class QuizChain:
    """
    出题链 - 通过 Prompt 引导 LLM 输出 JSON，手动解析

    DeepSeek 不支持 with_structured_output，因此统一使用
    Prompt 要求 JSON 格式 + 解析 JSON 的方式。
    """

    def __init__(self, llm, prompt):
        self.llm = llm
        self.prompt = prompt

    async def ainvoke(self, inputs: dict) -> QuizResponse:
        chain = self.prompt | self.llm
        result = await chain.ainvoke(inputs)
        parsed = safe_parse_json(result.content)
        if parsed is not None:
            return QuizResponse(**parsed)
        # 极端兜底：返回空题目
        logger.error("QuizChain.ainvoke JSON 解析彻底失败，返回空题")
        return QuizResponse(questions=[], metadata={
            "subject": inputs.get("subject", ""),
            "topic": inputs.get("topic", ""),
            "generatedAt": "",
            "model": "deepseek-chat",
            "searchEnhanced": False,
            "searchSources": [],
        })

    def invoke(self, inputs: dict) -> QuizResponse:
        chain = self.prompt | self.llm
        result = chain.invoke(inputs)
        parsed = safe_parse_json(result.content)
        if parsed is not None:
            return QuizResponse(**parsed)
        logger.error("QuizChain.invoke JSON 解析彻底失败，返回空题")
        return QuizResponse(questions=[], metadata={
            "subject": inputs.get("subject", ""),
            "topic": inputs.get("topic", ""),
            "generatedAt": "",
            "model": "deepseek-chat",
            "searchEnhanced": False,
            "searchSources": [],
        })


# ============================================================
# SearchAugmentedQuizChain — Agent 驱动 + JSON 手动解析
# ============================================================

class SearchAugmentedQuizChain:
    """
    搜索增强出题链 - Agent 驱动

    AI Agent 拥有 TavilySearch 和 TavilyExtract 两个工具，
    可以自主决定搜索策略。最终输出使用 JSON 手动解析。
    """

    def __init__(self, llm):
        self.llm = llm

    async def ainvoke(self, inputs: dict) -> QuizResponse:
        """异步执行搜索增强出题"""
        try:
            tavily_search = TavilySearch(max_results=5, topic="general")
            tavily_extract = TavilyExtract()

            agent = create_agent(
                model=self.llm,
                tools=[tavily_search, tavily_extract],
                system_prompt=SEARCH_QUIZ_SYSTEM_PROMPT,
            )

            human_prompt = SEARCH_QUIZ_HUMAN_PROMPT.format(**inputs)
            result = await agent.ainvoke({
                "messages": [{"role": "user", "content": human_prompt}]
            })

            # 获取 Agent 最终输出内容
            final_message = result["messages"][-1]
            content = final_message.content if hasattr(final_message, 'content') else str(final_message)

            # 方案 1：直接解析 Agent 输出中的 JSON
            parsed = safe_parse_json(content)
            if parsed is not None:
                return QuizResponse(**parsed)

            # 方案 2：让 LLM 重新格式化输出为 JSON（不使用 with_structured_output）
            reformat_prompt = ChatPromptTemplate.from_messages([
                ("system", "你是一个 JSON 格式化助手。请将用户输入的内容整理为指定的 JSON 格式输出，不要添加额外说明。"),
                ("human", QUIZ_SYSTEM_PROMPT + f"\n\n请将以下出题内容整理为上述 JSON 格式：\n\n{content}"),
            ])
            chain = reformat_prompt | self.llm
            reformat_result = await chain.ainvoke({})
            parsed = safe_parse_json(reformat_result.content)
            if parsed is not None:
                return QuizResponse(**parsed)

            # 方案 3（降级到传统链）：JSON 彻底解析失败
            logger.warning("搜索增强出题 JSON 解析失败，降级到传统链")
            fallback_llm = _create_llm(timeout=90)
            fallback_prompt = ChatPromptTemplate.from_messages([
                ("system", QUIZ_SYSTEM_PROMPT),
                ("human", QUIZ_HUMAN_PROMPT),
            ])
            fallback_chain = QuizChain(fallback_llm, fallback_prompt)
            return await fallback_chain.ainvoke(inputs)

        except Exception as e:
            logger.warning("搜索增强出题异常，降级到传统链: %s", str(e))
            fallback_llm = _create_llm(timeout=90)
            fallback_prompt = ChatPromptTemplate.from_messages([
                ("system", QUIZ_SYSTEM_PROMPT),
                ("human", QUIZ_HUMAN_PROMPT),
            ])
            fallback_chain = QuizChain(fallback_llm, fallback_prompt)
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
