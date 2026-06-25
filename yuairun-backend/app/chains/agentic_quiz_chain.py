"""Agentic RAG 出题链 — AI 自主判断检索方式（非 Agent 框架版）"""

import json
import logging
import os

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from app.config import get_settings
from app.models.quiz import QuizResponse
from app.prompts.quiz_prompt import (
    QUIZ_SYSTEM_PROMPT,
    QUIZ_HUMAN_PROMPT,
)
from app.tools.kb_retriever import KnowledgeBaseRetriever
from app.chains.quiz_chain import (
    _create_llm,
    safe_parse_json,
    QuizChain,
)

logger = logging.getLogger(__name__)

# ============================================================
# Strategy Decision Prompt — AI 分析 topic 决定检索策略
# ============================================================

STRATEGY_DECISION_PROMPT = """你是一个智能检索策略决策专家。请根据用户输入的学习内容，判断最合适的检索策略。

## 用户输入
- 学科：{subject}
- 知识点：{topic}
- 知识库：{kb_info}

## 请分析并输出你的决策：

{strategy_guide}

## 输出格式
请严格输出以下 JSON 格式，不要添加额外说明：
{{
  "reasoning": "你的分析推理过程（一句话概括）",
  "strategy": "retrieval_strategy_choice",
  "search_query": "优化后的搜索关键词（用于联网搜索）",
  "search_depth": "basic 或 advanced",
  "max_results": 3-8之间的数字,
  "need_extract": true或false,
  "kb_k": 5（知识库检索条数，如无知识库则忽略）
}}

其中 strategy 可选值：
- "kb_only": 仅知识库检索（topic 成熟、知识库内容充分）
- "web_only": 仅联网搜索（无知识库 或 topic 需要最新信息）
- "kb_then_web": 先知识库，不足时补充联网搜索
- "web_then_kb": 先联网搜索，不足时补充知识库"""


# ============================================================
# Agentic Quiz Chain — 先决策再执行的可靠架构
# ============================================================

class AgenticQuizChain:
    """
    Agentic RAG 出题链（非 Agent 框架）

    采用"先决策→再执行→后出题"的三阶段架构：
    1. AI 分析 topic 决定最优检索策略（JSON 输出）
    2. 代码按策略执行检索（ChromaDB / Tavily / 两者都有）
    3. AI 基于检索结果生成带来源标签的题目

    这种设计不依赖 DeepSeek 的 Agent 工具调用能力，更可靠。
    """

    def __init__(
        self,
        knowledge_base_id: str | None = None,
        knowledge_base_name: str = "",
    ):
        self.knowledge_base_id = knowledge_base_id
        self.knowledge_base_name = knowledge_base_name
        self.llm = _create_llm(timeout=90)

    async def ainvoke(self, inputs: dict) -> QuizResponse:
        """异步执行三阶段 Agentic RAG 出题"""
        try:
            has_kb = bool(self.knowledge_base_id)

            # ====================================================
            # Phase 1: AI 决策检索策略
            # ====================================================
            strategy = await self._decide_strategy(inputs, has_kb)
            logger.info(
                "Agentic 决策结果: strategy=%s, query=%s, has_kb=%s",
                strategy.get("strategy", "unknown"),
                strategy.get("search_query", inputs.get("topic", "")),
                has_kb,
            )

            strategy_name = strategy.get("strategy", "web_only")
            search_query = strategy.get("search_query", inputs.get("topic", ""))

            # ====================================================
            # Phase 2: 按策略执行检索
            # ====================================================
            kb_context = ""
            web_context = ""
            search_sources: list[str] = []
            tools_used: list[str] = []

            # 2a. 知识库检索
            should_search_kb = strategy_name in ("kb_only", "kb_then_web", "web_then_kb") and has_kb
            if should_search_kb:
                kb_k = strategy.get("kb_k", 5)
                kb_context, kb_sources = await self._retrieve_kb(
                    query=search_query,
                    k=kb_k,
                )
                if kb_context:
                    tools_used.append("knowledge_base_retriever")
                    search_sources.extend(kb_sources)

            # 2b. 联网搜索（无知识库时自动走此路，有知识库但策略允许时也走）
            should_search_web = strategy_name in ("web_only", "kb_then_web", "web_then_kb")
            if should_search_web:
                search_depth = strategy.get("search_depth", "basic")
                max_results = strategy.get("max_results", 5)
                web_context, web_sources = await self._search_web(
                    query=search_query,
                    search_depth=search_depth,
                    max_results=max_results,
                )
                if web_context:
                    tools_used.append("TavilySearch")
                    search_sources.extend(web_sources)

            # ====================================================
            # Phase 3: 基于材料出题
            # ====================================================
            has_material = bool(kb_context or web_context)
            if not has_material:
                logger.info("Agentic 检索无结果，模型知识出题")
                return await self._fallback(inputs, fallback_reason="no_material")

            result = await self._generate_quiz(
                inputs=inputs,
                kb_context=kb_context,
                web_context=web_context,
                has_kb=has_kb,
                strategy_name=strategy_name,
                tools_used=tools_used,
                search_sources=search_sources,
            )
            return result

        except Exception as e:
            logger.warning("AgenticRAG 出题异常，降级到传统链: %s", str(e))
            return await self._fallback(inputs, fallback_reason=f"exception: {e}")

    # ============================================================
    # Phase 1: 策略决策
    # ============================================================

    async def _decide_strategy(self, inputs: dict, has_kb: bool) -> dict:
        """AI 分析 topic 并决定检索策略"""
        if has_kb:
            strategy_guide = (
                f"用户已选择知识库「{self.knowledge_base_name or self.knowledge_base_id}」。\n"
                "请判断：\n"
                "1. 如果 topic 是成熟/经典知识（知识库很可能有）→ 'kb_only' 或 'kb_then_web'\n"
                "2. 如果 topic 是新兴/前沿知识（知识库可能没有）→ 'web_then_kb' 或 'web_only'\n"
                "3. 默认推荐 'kb_then_web'：先尝试知识库，如果内容不足再补充联网搜索"
            )
        else:
            strategy_guide = (
                "用户未选择知识库。\n"
                "请判断：\n"
                "1. 默认使用 'web_only' → 联网搜索获取最新资料\n"
                "2. 如果 topic 只需要简单知识，用 'basic' 搜索深度即可\n"
                "3. 如果 topic 复杂专业，用 'advanced' 深度和更多结果"
            )

        kb_info_text = (
            f"{self.knowledge_base_name or self.knowledge_base_id}" if has_kb else "未选择"
        )

        prompt = STRATEGY_DECISION_PROMPT.format(
            subject=inputs.get("subject", ""),
            topic=inputs.get("topic", ""),
            kb_info=kb_info_text,
            strategy_guide=strategy_guide,
        )

        result = await self.llm.ainvoke(prompt)
        parsed = safe_parse_json(result.content)

        if parsed is None or "strategy" not in parsed:
            logger.warning("策略决策解析失败，使用默认策略 web_only")
            return {
                "strategy": "web_only",
                "search_query": inputs.get("topic", ""),
                "search_depth": "basic",
                "max_results": 5,
                "need_extract": False,
                "kb_k": 5,
            }

        return parsed

    # ============================================================
    # Phase 2: 执行检索
    # ============================================================

    async def _retrieve_kb(self, query: str, k: int = 5) -> tuple[str, list[str]]:
        """从知识库检索"""
        try:
            retriever = KnowledgeBaseRetriever(
                kb_id=self.knowledge_base_id,
                kb_name=self.knowledge_base_name,
            )
            result_text = await retriever._arun(query=query, k=k)

            if "检索结果为空" in result_text or "检索异常" in result_text:
                logger.info("知识库检索无结果: %s", self.knowledge_base_id)
                return "", []

            # 提取来源
            sources = []
            for line in result_text.split("\n"):
                if line.startswith("来源："):
                    sources.append(line.replace("来源：", "").strip())

            return result_text, sources

        except Exception as e:
            logger.warning("知识库检索失败: %s", e)
            return "", []

    async def _search_web(
        self,
        query: str,
        search_depth: str = "basic",
        max_results: int = 5,
    ) -> tuple[str, list[str]]:
        """联网搜索（使用 Tavily Search API）"""
        try:
            settings = get_settings()
            if not settings.tavily_api_key:
                logger.warning("Tavily API Key 未配置，跳过联网搜索")
                return "", []

            import httpx

            # 直接调用 Tavily Search API（更可靠，无需 LangChain Agent 工具调用）
            url = "https://api.tavily.com/search"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {settings.tavily_api_key}",
            }
            payload = {
                "query": query,
                "search_depth": search_depth,
                "max_results": max_results,
                "topic": "general",
                "include_answer": False,
                "include_raw_content": False,
            }

            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()

            results = data.get("results", [])
            if not results:
                logger.info("Tavily 搜索无结果: %s", query)
                return "", []

            lines = []
            sources = []
            for i, item in enumerate(results, 1):
                title = item.get("title", "")
                url = item.get("url", "")
                content = item.get("content", "")
                lines.append(f"--- 搜索结果 {i} ---")
                lines.append(f"标题：{title}")
                lines.append(f"来源：{url}")
                lines.append(f"内容：{content}")
                lines.append("")
                if url:
                    sources.append(url)

            context = "\n".join(lines)
            logger.info("Tavily 搜索成功: %d 条结果", len(results))
            return context, sources

        except Exception as e:
            logger.warning("联网搜索失败: %s", e)
            return "", []

    # ============================================================
    # Phase 3: 基于材料出题
    # ============================================================

    async def _generate_quiz(
        self,
        inputs: dict,
        kb_context: str,
        web_context: str,
        has_kb: bool,
        strategy_name: str,
        tools_used: list[str],
        search_sources: list[str],
    ) -> QuizResponse:
        """基于检索到的材料出题"""
        # 构建增强 Prompt
        context_parts = []
        if kb_context:
            context_parts.append(f"## 知识库参考资料\n{kb_context}")
        if web_context:
            context_parts.append(f"## 联网搜索参考资料\n{web_context}")

        context_text = "\n\n".join(context_parts)
        has_mixed = bool(kb_context and web_context)

        # 构建来源标签指南
        if has_mixed:
            source_guide = (
                "你既有知识库资料又有联网搜索结果。请按以下规则为每道题标注 knowledgeSource：\n"
                "- 基于知识库资料的题目 → 'knowledge_base'\n"
                "- 基于联网搜索结果的题目 → 'web_search'\n"
                "- 基于模型自身知识的题目 → 'model_knowledge'"
            )
        elif kb_context:
            source_guide = (
                "你只有知识库资料。请基于知识库内容出题。\n"
                "每道题的 knowledgeSource 标注为 'knowledge_base'。\n"
                "如果知识库内容不足以生成足够题目，可以补充模型知识并标注 'model_knowledge'。"
            )
        else:
            source_guide = (
                "你只有联网搜索结果。请基于搜索结果出题。\n"
                "每道题的 knowledgeSource 标注为 'web_search'。\n"
                "如果搜索内容不足以生成足够题目，可以补充模型知识并标注 'model_knowledge'。"
            )

        enhanced_prompt = QUIZ_SYSTEM_PROMPT + f"""

## 参考资料
{context_text}

## 知识来源标注要求
{source_guide}

## 元数据要求
在 metadata 中设置：
- searchEnhanced: true
- searchMode: "agentic"
- searchSources: {json.dumps(search_sources)}
"""

        human_prompt = QUIZ_HUMAN_PROMPT.format(**inputs)

        full_prompt = enhanced_prompt + "\n\n" + human_prompt
        result = await self.llm.ainvoke(full_prompt)

        parsed = safe_parse_json(result.content)
        if parsed is not None:
            quiz_response = QuizResponse(**parsed)
            # 补充元数据
            if quiz_response.metadata:
                quiz_response.metadata.searchMode = "agentic"
                quiz_response.metadata.searchEnhanced = True
                quiz_response.metadata.toolsInvoked = tools_used
                quiz_response.metadata.searchSources = search_sources
                if has_kb:
                    quiz_response.metadata.knowledgeBaseId = self.knowledge_base_id
                    quiz_response.metadata.knowledgeBaseName = self.knowledge_base_name
                quiz_response.metadata.retrievalStrategy = strategy_name
            return quiz_response

        # JSON 解析失败，降级
        logger.warning("AgenticRAG 出题 JSON 解析失败，降级到传统链")
        return await self._fallback(inputs, fallback_reason="json_parse_failed")

    async def _fallback(self, inputs: dict, fallback_reason: str = "") -> QuizResponse:
        """降级到传统出题链"""
        logger.warning("AgenticRAG 降级（%s）", fallback_reason)
        fallback_llm = _create_llm(timeout=90)
        fallback_prompt = ChatPromptTemplate.from_messages([
            ("system", QUIZ_SYSTEM_PROMPT),
            ("human", QUIZ_HUMAN_PROMPT),
        ])
        fallback_chain = QuizChain(fallback_llm, fallback_prompt)
        result = await fallback_chain.ainvoke(inputs)
        result.metadata.searchMode = "agentic"
        result.metadata.searchEnhanced = False
        result.metadata.fallback = True
        return result

    def invoke(self, inputs: dict) -> QuizResponse:
        """同步执行"""
        import asyncio
        return asyncio.run(self.ainvoke(inputs))
