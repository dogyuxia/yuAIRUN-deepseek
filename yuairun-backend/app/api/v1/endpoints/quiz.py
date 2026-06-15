"""题目和分析报告 API 端点"""

from fastapi import APIRouter

from app.models.quiz import GenerateQuizRequest, GenerateQuizResponse
from app.models.report import AnalyzeQuizRequest, AnalyzeQuizResponse
from app.services.quiz_service import generate_quiz
from app.services.report_service import analyze_quiz

router = APIRouter(prefix="/api/quiz", tags=["quiz"])


@router.post("/generate", response_model=GenerateQuizResponse)
async def generate_quiz_endpoint(request: GenerateQuizRequest):
    """
    AI 生成题目

    根据用户输入的知识点和参数，AI 生成一套练习题。
    """
    return await generate_quiz(request)


@router.post("/analyze", response_model=AnalyzeQuizResponse)
async def analyze_quiz_endpoint(request: AnalyzeQuizRequest):
    """
    AI 生成分析报告

    根据答题数据，AI 生成个性化学习分析报告。
    """
    return await analyze_quiz(request)
