"""题目相关的 Pydantic 数据模型"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Literal


class QuizOption(BaseModel):
    """选项"""
    label: str = Field(description="选项标签，如 A/B/C/D")
    content: str = Field(description="选项内容")


class QuizQuestion(BaseModel):
    """单道题目"""
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(description="题目唯一ID")
    type: Literal["single", "multiple", "judge"] = Field(description="题目类型: single=单选, multiple=多选, judge=判断")
    question: str = Field(description="题目内容")
    options: list[QuizOption] = Field(description="选项列表")
    answer: str | list[str] = Field(description="正确答案，单选为字符串如'A'，多选为列表如['A','C']")
    explanation: str = Field(description="题目解析")
    difficulty: Literal["easy", "medium", "hard"] = Field(description="难度")
    knowledgePoint: str = Field(validation_alias="knowledgePoint", description="知识点标签")
    # 🆕 搜索增强：知识来源
    knowledgeSource: Literal["web_search", "model_knowledge", "knowledge_base"] = Field(
        default="model_knowledge",
        validation_alias="knowledgeSource",
        description="知识来源: web_search=基于搜索结果, model_knowledge=基于模型知识, knowledge_base=基于知识库",
    )


class QuizMetadata(BaseModel):
    """题目元数据"""
    model_config = ConfigDict(populate_by_name=True)

    subject: str = Field(description="学科")
    topic: str = Field(description="知识点")
    generatedAt: str = Field(validation_alias="generatedAt", description="生成时间")
    model: str = Field(description="使用的模型")
    # 🆕 搜索增强：是否使用了搜索增强
    searchEnhanced: bool = Field(
        default=False,
        validation_alias="searchEnhanced",
        description="是否使用了搜索增强",
    )
    # 🆕 搜索增强：搜索来源 URL 列表
    searchSources: list[str] = Field(
        default=[],
        validation_alias="searchSources",
        description="搜索来源 URL 列表",
    )
    # 🆕 RAG 知识库：搜索模式
    searchMode: str = Field(
        default="search",
        validation_alias="searchMode",
        description="搜索模式: search/knowledge_base/hybrid",
    )
    # 🆕 RAG 知识库：使用的知识库ID
    knowledgeBaseId: str | None = Field(
        default=None,
        validation_alias="knowledgeBaseId",
        description="使用的知识库ID",
    )
    # 🆕 RAG 知识库：使用的知识库名称
    knowledgeBaseName: str | None = Field(
        default=None,
        validation_alias="knowledgeBaseName",
        description="使用的知识库名称",
    )


class QuizResponse(BaseModel):
    """AI 生成的题目响应（绑定给结构化输出的模型）"""
    model_config = ConfigDict(populate_by_name=True)

    questions: list[QuizQuestion] = Field(description="生成的题目列表")
    metadata: QuizMetadata = Field(description="元数据")


# ---- API 请求/响应 ----

class GenerateQuizRequest(BaseModel):
    """生成题目请求"""
    subject: str = Field(description="学科类别", examples=["计算机网络"])
    topic: str = Field(description="知识点/内容描述", examples=["TCP三次握手的过程和原理"])
    count: int = Field(default=5, ge=1, le=20, description="题目数量")
    difficulty: Literal["easy", "medium", "hard", "mixed"] = Field(default="medium", description="难度")
    type: Literal["single", "multiple", "judge", "mixed"] = Field(default="single", description="题目类型")
    # 🆕 RAG 知识库
    knowledgeBaseId: str | None = Field(
        default=None,
        description="知识库ID，指定后从该知识库检索资料出题",
    )
    searchMode: Literal["search", "knowledge_base", "hybrid"] = Field(
        default="search",
        description="搜索模式: search=AI搜索, knowledge_base=仅知识库, hybrid=混合",
    )


class GenerateQuizResponse(BaseModel):
    """生成题目响应"""
    success: bool = Field(default=True)
    data: QuizResponse | None = None
    error: str | None = None
    detail: str | None = None
