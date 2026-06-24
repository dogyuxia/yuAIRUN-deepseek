"""出题业务逻辑"""

import logging
from datetime import datetime, timezone

from app.config import get_settings
from app.models.quiz import (
    GenerateQuizRequest,
    GenerateQuizResponse,
    QuizResponse,
)
from app.chains.quiz_chain import create_quiz_chain, create_search_augmented_quiz_chain
from app.chains.rag_quiz_chain import RAGQuizChain
from app.db.session import DbSession
from app.db.models.knowledge_base import KnowledgeBaseModel
from sqlalchemy import select

logger = logging.getLogger(__name__)


async def _lookup_kb_name(kb_id: str) -> str:
    """从数据库查询知识库名称，失败时返回 kb_id"""
    try:
        async with DbSession() as session:
            result = await session.execute(
                select(KnowledgeBaseModel).where(KnowledgeBaseModel.id == kb_id)
            )
            kb = result.scalar_one_or_none()
            return kb.name if kb else kb_id
    except Exception:
        return kb_id


async def generate_quiz(request: GenerateQuizRequest) -> GenerateQuizResponse:
    """
    根据用户输入生成题目

    根据 searchMode 路由到不同出题链：
    - "search" → Tavily 搜索增强出题链（默认）
    - "knowledge_base" → ChromaDB RAG 出题链
    - "hybrid" → 知识库 + 网络搜索混合出题链

    Args:
        request: 出题请求参数

    Returns:
        出题响应
    """
    settings = get_settings()

    try:
        # 处理难度和类型参数
        difficulty = request.difficulty
        if difficulty == "mixed":
            difficulty = "mixed（包含简单、中等、困难）"

        q_type = request.type
        if q_type == "mixed":
            q_type = "mixed（包含单选、多选、判断）"

        # 基础输入
        chain_inputs = {
            "subject": request.subject,
            "topic": request.topic,
            "count": request.count,
            "difficulty": difficulty,
            "type": q_type,
        }

        if settings.use_mock_llm:
            chain = create_quiz_chain(use_mock=True)
            result: QuizResponse = await chain.ainvoke(chain_inputs)
            result.metadata.searchEnhanced = False
            result.metadata.searchSources = []
            result.metadata.searchMode = request.searchMode
        else:
            if request.searchMode == "knowledge_base" and request.knowledgeBaseId:
                # RAG 知识库出题
                kb_name = await _lookup_kb_name(request.knowledgeBaseId)
                chain = RAGQuizChain(
                    kb_id=request.knowledgeBaseId,
                    kb_name=kb_name,
                )
                result = await chain.ainvoke(chain_inputs)
                
                # 如果 RAG 检索无结果，返回明确提示
                if not result.questions:
                    return GenerateQuizResponse(
                        success=False,
                        error="知识库中没有足够的相关内容，请尝试其他知识库或使用 AI 搜索模式",
                    )
                    
            elif request.searchMode == "hybrid" and request.knowledgeBaseId:
                # 混合模式：知识库 + 网络搜索（先用 RAG 再走搜索）
                kb_name = await _lookup_kb_name(request.knowledgeBaseId)
                rag_chain = RAGQuizChain(
                    kb_id=request.knowledgeBaseId,
                    kb_name=kb_name,
                )
                rag_result = await rag_chain.ainvoke(chain_inputs)
                
                # 补充网络搜索
                search_chain = create_search_augmented_quiz_chain()
                search_result = await search_chain.ainvoke(chain_inputs)
                
                # 合并两套题目（去重后取高质量）
                all_questions = []
                seen = set()
                for q in (rag_result.questions or []) + (search_result.questions or []):
                    if q.question not in seen:
                        seen.add(q.question)
                        all_questions.append(q)
                
                # 使用 RAG 结果的 metadata
                result = rag_result
                result.questions = all_questions[:request.count]
                result.metadata.searchMode = "hybrid"
                if rag_result.metadata and search_result.metadata:
                    result.metadata.searchSources = (
                        (rag_result.metadata.searchSources or []) +
                        (search_result.metadata.searchSources or [])
                    )
            else:
                # 默认：搜索增强出题
                chain = create_search_augmented_quiz_chain()
                result: QuizResponse = await chain.ainvoke(chain_inputs)
                result.metadata.searchMode = request.searchMode

        # 补充前端需要的字段
        for i, q in enumerate(result.questions, 1):
            if not q.id:
                q.id = f"q_{i:03d}"
            if not q.knowledgeSource:
                q.knowledgeSource = "model_knowledge"

        result.metadata.generatedAt = datetime.now(timezone.utc).isoformat()

        return GenerateQuizResponse(success=True, data=result)

    except Exception as e:
        logger.error("Quiz generation failed: %s", str(e))
        return GenerateQuizResponse(
            success=False,
            error="AI 生成题目失败，请重试",
            detail=str(e),
        )
