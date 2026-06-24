"""RAG 出题链 — 基于知识库检索 + JSON 手动解析"""

import logging

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from app.config import get_settings
from app.models.quiz import QuizResponse
from app.prompts.rag_quiz_prompt import (
    RAG_QUIZ_SYSTEM_PROMPT,
    RAG_QUIZ_HUMAN_PROMPT,
    HYBRID_QUIZ_SYSTEM_PROMPT,
)
from app.services.vector_service import search_similar_chunks
from app.chains.quiz_chain import safe_parse_json

logger = logging.getLogger(__name__)


def _create_llm(timeout: int = 120):
    """创建 DeepSeek LLM 实例"""
    settings = get_settings()
    return ChatOpenAI(
        model="deepseek-chat",
        openai_api_key=settings.deepseek_api_key,
        openai_api_base=settings.deepseek_base_url,
        temperature=0.7,
        timeout=timeout,
        max_retries=2,
    )


class RAGQuizChain:
    """
    RAG 出题链

    1. 从 ChromaDB 检索与 topic 相关的知识块
    2. 将知识块作为上下文注入 Prompt
    3. 通过 Prompt 要求 JSON 输出，手动解析

    注意：DeepSeek API 不支持 with_structured_output，
    因此统一使用 Prompt 引导 JSON 格式 + 手动解析。
    """

    def __init__(self, kb_id: str, kb_name: str = ""):
        self.kb_id = kb_id
        self.kb_name = kb_name
        self.llm = _create_llm()

    async def ainvoke(self, inputs: dict) -> QuizResponse:
        """异步执行 RAG 出题"""
        try:
            topic = inputs.get("topic", "")

            # 1. 从知识库检索相关内容
            chunks = await search_similar_chunks(
                query=topic,
                kb_id=self.kb_id,
                k=5,
            )

            if not chunks:
                logger.warning("知识库检索无结果 (kb: %s, topic: %s)", self.kb_id, topic)
                return QuizResponse(
                    questions=[],
                    metadata={
                        "subject": inputs.get("subject", ""),
                        "topic": topic,
                        "generatedAt": "",
                        "model": "deepseek-chat",
                        "searchEnhanced": False,
                        "searchMode": "knowledge_base",
                        "searchSources": [],
                        "knowledgeBaseId": self.kb_id,
                        "knowledgeBaseName": self.kb_name,
                    },
                )

            # 2. 组装搜索上下文文本
            search_lines = []
            for i, chunk in enumerate(chunks, 1):
                source = chunk["metadata"].get("filename", "未知来源")
                search_lines.append(f"--- 知识库资料 {i} ---")
                search_lines.append(f"来源：{source}")
                search_lines.append(f"内容：{chunk['text']}")
                search_lines.append("")

            search_context = "\n".join(search_lines)
            search_sources = [
                chunk["metadata"].get("filename", "未知来源")
                for chunk in chunks
            ]

            # 3. 构建 Prompt（手动拼接，避免 LangChain 模板解析 `{}` 代码块出错）
            chain_inputs = {
                **inputs,
                "search_context": search_context,
                "knowledge_base_name": self.kb_name or self.kb_id,
            }

            prompt_text = RAG_QUIZ_SYSTEM_PROMPT.replace("{topic}", topic).replace("{search_context}", search_context)
            human_text = RAG_QUIZ_HUMAN_PROMPT.format(**chain_inputs)

            full_prompt = prompt_text + "\n\n" + human_text

            # 4. 调用 LLM（直接传字符串，跳过 ChatPromptTemplate 模板解析）
            result = await self.llm.ainvoke(full_prompt)
            parsed = safe_parse_json(result.content)

            if parsed is not None:
                quiz_response = QuizResponse(**parsed)
                # 补充 metadata
                if quiz_response.metadata:
                    quiz_response.metadata.searchEnhanced = True
                    quiz_response.metadata.searchMode = "knowledge_base"
                    quiz_response.metadata.searchSources = search_sources
                    quiz_response.metadata.knowledgeBaseId = self.kb_id
                    quiz_response.metadata.knowledgeBaseName = self.kb_name
                return quiz_response

            # JSON 解析失败，返回空题
            logger.error("RAG 出题 JSON 解析失败，返回空题")
            return QuizResponse(
                questions=[],
                metadata={
                    "subject": inputs.get("subject", ""),
                    "topic": topic,
                    "generatedAt": "",
                    "model": "deepseek-chat",
                    "searchEnhanced": False,
                    "searchMode": "knowledge_base",
                    "searchSources": search_sources,
                    "knowledgeBaseId": self.kb_id,
                    "knowledgeBaseName": self.kb_name,
                },
            )

        except Exception as e:
            logger.error("RAG 出题失败: %s", e)
            return QuizResponse(
                questions=[],
                metadata={
                    "subject": inputs.get("subject", ""),
                    "topic": inputs.get("topic", ""),
                    "generatedAt": "",
                    "model": "deepseek-chat",
                    "searchEnhanced": False,
                    "searchMode": "knowledge_base",
                    "searchSources": [],
                    "knowledgeBaseId": self.kb_id,
                    "knowledgeBaseName": self.kb_name,
                },
            )

    def invoke(self, inputs: dict) -> QuizResponse:
        """同步执行 RAG 出题"""
        import asyncio
        return asyncio.run(self.ainvoke(inputs))
