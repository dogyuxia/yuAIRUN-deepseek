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

logger = logging.getLogger(__name__)


async def generate_quiz(request: GenerateQuizRequest) -> GenerateQuizResponse:
    """
    根据用户输入生成题目

    使用搜索增强 Agent 驱动出题：
    1. AI Agent 收到用户输入（关键词或 URL）
    2. AI 自主决定调用 TavilySearch（搜索）或 TavilyExtract（提取 URL 内容）
    3. AI 动态调整搜索参数（search_depth、max_results、time_range 等）
    4. 基于收集的资料生成题目
    5. 搜索失败时自动降级为纯模型知识出题

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

        if settings.use_mock_llm:
            # Mock 模式：传统链（无搜索）
            chain = create_quiz_chain(use_mock=True)
            result: QuizResponse = await chain.ainvoke({
                "subject": request.subject,
                "topic": request.topic,
                "count": request.count,
                "difficulty": difficulty,
                "type": q_type,
            })
            # Mock 模式下标记搜索增强为 false
            result.metadata.searchEnhanced = False
            result.metadata.searchSources = []
        else:
            # 生产模式：搜索增强 Agent 链（始终开启搜索增强）
            chain = create_search_augmented_quiz_chain()
            result: QuizResponse = await chain.ainvoke({
                "subject": request.subject,
                "topic": request.topic,
                "count": request.count,
                "difficulty": difficulty,
                "type": q_type,
            })

        # 补充前端需要的字段
        for i, q in enumerate(result.questions, 1):
            if not q.id:
                q.id = f"q_{i:03d}"
            # 确保每道题都有 knowledgeSource
            if not q.knowledgeSource:
                q.knowledgeSource = "model_knowledge"

        # 更新生成时间
        result.metadata.generatedAt = datetime.now(timezone.utc).isoformat()

        return GenerateQuizResponse(success=True, data=result)

    except Exception as e:
        logger.error("Quiz generation failed: %s", str(e))
        return GenerateQuizResponse(
            success=False,
            error="AI 生成题目失败，请重试",
            detail=str(e),
        )
