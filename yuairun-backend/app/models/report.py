"""分析报告相关的 Pydantic 数据模型"""

from pydantic import BaseModel, Field, ConfigDict
from app.models.quiz import QuizQuestion


class AnalyzeQuizRequest(BaseModel):
    """分析报告请求"""
    model_config = ConfigDict(populate_by_name=True)

    subject: str = Field(description="学科")
    topic: str = Field(description="知识点")
    questions: list[QuizQuestion] = Field(description="题目列表")
    userAnswers: dict[str, str | list[str]] = Field(validation_alias="userAnswers", description="用户答案 {question_id: answer}")
    duration: int = Field(default=0, description="答题用时（秒）")


class AnalyzeReportData(BaseModel):
    """AI 生成的分析报告数据（绑定给结构化输出的模型）"""
    model_config = ConfigDict(populate_by_name=True)

    summary: str = Field(description="整体评估")
    score: int = Field(description="得分 (0-100)", ge=0, le=100)
    accuracy: float = Field(description="正确率 (0-1)", ge=0, le=1)
    weakPoints: list[str] = Field(validation_alias="weakPoints", description="薄弱知识点")
    strongPoints: list[str] = Field(validation_alias="strongPoints", description="掌握较好的知识点")
    suggestions: list[str] = Field(description="学习建议")
    recommendedTopics: list[str] = Field(validation_alias="recommendedTopics", description="推荐练习的知识点")
    detailedAnalysis: str = Field(validation_alias="detailedAnalysis", description="详细分析（Markdown 格式）")


class AnalyzeQuizResponse(BaseModel):
    """分析报告响应"""
    success: bool = Field(default=True)
    data: AnalyzeReportData | None = None
    error: str | None = None
