"""出题业务逻辑"""

import logging
from datetime import datetime, timezone

from app.config import get_settings
from app.models.quiz import (
    GenerateQuizRequest,
    GenerateQuizResponse,
    QuizResponse,
)
from app.chains.quiz_chain import create_quiz_chain, create_agentic_quiz_chain
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

    使用 Agentic RAG 出题链，AI 自主判断检索策略：
    - 有知识库时优先检索知识库，不充分则补充联网搜索
    - 无知识库时直接联网搜索
    - 全部失败则使用模型知识降级

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
            result.metadata.searchMode = "agentic"
        else:
            # 统一使用 Agentic RAG 出题链
            kb_name = ""
            if request.knowledgeBaseId:
                kb_name = await _lookup_kb_name(request.knowledgeBaseId)

            chain = create_agentic_quiz_chain(
                knowledge_base_id=request.knowledgeBaseId,
                knowledge_base_name=kb_name,
            )
            result: QuizResponse = await chain.ainvoke(chain_inputs)

            # 如果无题目（Agent 返回空），返回明确提示
            if not result.questions:
                return GenerateQuizResponse(
                    success=False,
                    error="没有生成任何题目，请尝试修改知识点描述或更换出题方式",
                )

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
