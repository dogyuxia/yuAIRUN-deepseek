"""出题业务逻辑"""

from datetime import datetime, timezone

from app.config import get_settings
from app.models.quiz import (
    GenerateQuizRequest,
    GenerateQuizResponse,
    QuizResponse,
)
from app.chains.quiz_chain import create_quiz_chain


async def generate_quiz(request: GenerateQuizRequest) -> GenerateQuizResponse:
    """
    根据用户输入生成题目

    Args:
        request: 出题请求参数

    Returns:
        出题响应
    """
    settings = get_settings()

    try:
        # 根据配置决定使用 Mock 还是真实 LLM
        chain = create_quiz_chain(use_mock=settings.use_mock_llm)

        # 处理难度和类型参数
        difficulty = request.difficulty
        if difficulty == "mixed":
            difficulty = "mixed（包含简单、中等、困难）"

        q_type = request.type
        if q_type == "mixed":
            q_type = "mixed（包含单选、多选、判断）"

        # 调用链
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

        # 更新生成时间
        result.metadata.generatedAt = datetime.now(timezone.utc).isoformat()

        return GenerateQuizResponse(success=True, data=result)

    except Exception as e:
        return GenerateQuizResponse(
            success=False,
            error="AI 生成题目失败，请重试",
            detail=str(e),
        )
