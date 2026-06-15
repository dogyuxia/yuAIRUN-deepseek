"""分析报告业务逻辑"""

from app.config import get_settings
from app.models.quiz import QuizQuestion
from app.models.report import (
    AnalyzeQuizRequest,
    AnalyzeQuizResponse,
    AnalyzeReportData,
)
from app.chains.report_chain import create_report_chain, format_quiz_details


async def analyze_quiz(request: AnalyzeQuizRequest) -> AnalyzeQuizResponse:
    """
    根据答题数据生成分析报告

    Args:
        request: 分析报告请求

    Returns:
        分析报告响应
    """
    settings = get_settings()

    try:
        chain = create_report_chain(use_mock=settings.use_mock_llm)

        # 计算正确率
        total = len(request.questions)
        correct = 0
        for q in request.questions:
            qid = q.id
            user_ans = request.userAnswers.get(qid, "")
            correct_ans = q.answer

            if isinstance(correct_ans, list):
                if isinstance(user_ans, list) and sorted(user_ans) == sorted(correct_ans):
                    correct += 1
            else:
                if str(user_ans) == str(correct_ans):
                    correct += 1

        accuracy = correct / total if total > 0 else 0

        # 格式化题目详情
        questions_dict = [q.model_dump() for q in request.questions]
        quiz_details = format_quiz_details(questions_dict, request.userAnswers)

        # 调用链
        result: AnalyzeReportData = await chain.ainvoke({
            "subject": request.subject,
            "topic": request.topic,
            "duration": request.duration,
            "accuracy": round(accuracy * 100, 1),
            "quiz_details": quiz_details,
            "questions": questions_dict,
            "userAnswers": request.userAnswers,
        })

        return AnalyzeQuizResponse(success=True, data=result)

    except Exception as e:
        return AnalyzeQuizResponse(
            success=False,
            error="AI 生成分析报告失败，请重试",
        )
