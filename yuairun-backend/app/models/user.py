"""用户系统相关的 Pydantic 数据模型"""

from pydantic import BaseModel, Field
from typing import Optional


# ============================================================
# 请求模型
# ============================================================

class LoginRequest(BaseModel):
    """微信登录请求"""
    code: str = Field(description="微信临时登录凭证")
    nickname: Optional[str] = Field(default=None, description="微信昵称（可选）")
    avatarUrl: Optional[str] = Field(default=None, validation_alias="avatarUrl", description="微信头像 URL（可选）")


class RefreshTokenRequest(BaseModel):
    """刷新 Token 请求"""
    token: str = Field(description="旧 JWT Token")


class UpdateProfileRequest(BaseModel):
    """更新用户信息请求"""
    nickname: Optional[str] = Field(default=None, description="新昵称")


class HistorySyncRecord(BaseModel):
    """单条闯关同步记录"""
    subject: str = Field(description="学科")
    topic: str = Field(description="知识点")
    questions: list[dict] = Field(description="完整题目列表")
    userAnswers: dict[str, str | list[str]] = Field(validation_alias="userAnswers", description="用户答案 {q_id: answer}")
    correctCount: int = Field(validation_alias="correctCount", ge=0, description="正确数")
    totalCount: int = Field(validation_alias="totalCount", ge=1, description="总题数")
    accuracy: float = Field(ge=0, le=1, description="正确率")
    duration: int = Field(default=0, ge=0, description="答题用时（秒）")
    createdAt: str = Field(validation_alias="createdAt", description="创建时间 ISO 格式")


class HistorySyncRequest(BaseModel):
    """批量同步闯关记录请求"""
    records: list[HistorySyncRecord] = Field(description="闯关记录列表")


class WrongBookSyncItem(BaseModel):
    """单条错题同步项"""
    question: dict = Field(description="完整题目对象")
    userAnswer: str = Field(validation_alias="userAnswer", description="用户当时的答案")
    correctAnswer: str = Field(validation_alias="correctAnswer", description="正确答案")
    subject: str = Field(description="学科")
    topic: str = Field(description="知识点")


class WrongBookSyncRequest(BaseModel):
    """批量同步错题请求"""
    items: list[WrongBookSyncItem] = Field(description="错题列表")


# ============================================================
# 响应模型
# ============================================================

class UserInfo(BaseModel):
    """用户基本信息"""
    id: str = Field(description="用户唯一ID")
    nickname: str = Field(description="微信昵称")
    avatarUrl: str = Field(validation_alias="avatarUrl", description="微信头像 URL")
    xp: int = Field(description="经验值")
    level: int = Field(description="等级")
    levelTitle: str = Field(validation_alias="levelTitle", description="等级称号")
    isNewUser: bool = Field(validation_alias="isNewUser", description="是否为新用户")


class UserStats(BaseModel):
    """用户学习统计"""
    totalQuizzes: int = Field(validation_alias="totalQuizzes", default=0, description="总闯关次数")
    totalQuestions: int = Field(validation_alias="totalQuestions", default=0, description="总答题数")
    totalCorrect: int = Field(validation_alias="totalCorrect", default=0, description="总正确数")
    totalWrong: int = Field(validation_alias="totalWrong", default=0, description="总错误数")
    accuracy: float = Field(default=0, description="总正确率")
    totalDuration: int = Field(validation_alias="totalDuration", default=0, description="总答题用时（秒）")
    streakDays: int = Field(validation_alias="streakDays", default=0, description="连续学习天数")
    lastActiveDate: Optional[str] = Field(validation_alias="lastActiveDate", default=None, description="最后活跃日期")


class LoginResponseData(BaseModel):
    """登录响应数据"""
    token: str = Field(description="JWT Token")
    expiresIn: int = Field(validation_alias="expiresIn", description="过期时间（秒）")
    user: UserInfo = Field(description="用户基本信息")


class ProfileResponseData(BaseModel):
    """个人中心响应数据"""
    id: str = Field(description="用户ID")
    nickname: str = Field(description="昵称")
    avatarUrl: str = Field(validation_alias="avatarUrl", description="头像 URL")
    xp: int = Field(description="经验值")
    level: int = Field(description="等级")
    levelTitle: str = Field(validation_alias="levelTitle", description="等级称号")
    nextLevelXp: int = Field(validation_alias="nextLevelXp", description="下一级所需经验值")
    stats: UserStats = Field(description="学习统计")
    recentHistories: list = Field(validation_alias="recentHistories", default=[], description="最近闯关记录")


class RefreshTokenResponseData(BaseModel):
    """刷新 Token 响应数据"""
    token: str = Field(description="新 JWT Token")
    expiresIn: int = Field(validation_alias="expiresIn", description="过期时间（秒）")


class HistoryListItem(BaseModel):
    """闯关历史列表项"""
    id: str = Field(description="记录ID")
    subject: str = Field(description="学科")
    topic: str = Field(description="知识点")
    questionCount: int = Field(validation_alias="questionCount", description="总题数")
    correctCount: int = Field(validation_alias="correctCount", description="正确数")
    accuracy: float = Field(description="正确率")
    duration: int = Field(description="答题用时（秒）")
    xpEarned: int = Field(validation_alias="xpEarned", default=0, description="获得经验值")
    createdAt: str = Field(validation_alias="createdAt", description="创建时间")


class HistoryDetailData(BaseModel):
    """闯关记录详情"""
    id: str = Field(description="记录ID")
    subject: str = Field(description="学科")
    topic: str = Field(description="知识点")
    questionCount: int = Field(validation_alias="questionCount", description="总题数")
    correctCount: int = Field(validation_alias="correctCount", description="正确数")
    accuracy: float = Field(description="正确率")
    duration: int = Field(description="答题用时（秒）")
    xpEarned: int = Field(validation_alias="xpEarned", default=0, description="获得经验值")
    answers: list[dict] = Field(default=[], description="答题详情列表")
    createdAt: str = Field(validation_alias="createdAt", description="创建时间")


class WrongBookListItem(BaseModel):
    """错题本列表项"""
    id: str = Field(description="记录ID")
    question: dict = Field(description="完整题目对象")
    userAnswer: str = Field(validation_alias="userAnswer", description="用户当时的答案")
    correctAnswer: str = Field(validation_alias="correctAnswer", description="正确答案")
    subject: str = Field(description="学科")
    topic: str = Field(description="知识点")
    wrongCount: int = Field(validation_alias="wrongCount", description="答错次数")
    lastWrongAt: str = Field(validation_alias="lastWrongAt", description="最近一次答错时间")
    isMastered: bool = Field(validation_alias="isMastered", default=False, description="是否已掌握")


class PaginatedResponse(BaseModel):
    """分页响应"""
    items: list = Field(description="数据列表")
    total: int = Field(description="总数")
    page: int = Field(description="当前页码")
    pageSize: int = Field(validation_alias="pageSize", description="每页数量")
    hasMore: bool = Field(validation_alias="hasMore", description="是否有更多")


class SyncResponseData(BaseModel):
    """同步响应数据"""
    syncedCount: int = Field(validation_alias="syncedCount", description="同步数量")
    totalCount: int = Field(validation_alias="totalCount", description="总数")
    xpEarned: int = Field(validation_alias="xpEarned", default=0, description="获得经验值")
    currentXp: int = Field(validation_alias="currentXp", default=0, description="当前经验值")
    currentLevel: int = Field(validation_alias="currentLevel", default=1, description="当前等级")


class ApiResponse(BaseModel):
    """通用 API 响应"""
    success: bool = Field(default=True)
    data: Optional[dict | BaseModel] = None
    error: Optional[str] = None


class ManualLoginRequest(BaseModel):
    """手动登录请求"""
    username: str = Field(..., min_length=6, max_length=6, description="6位用户名")
    password: str = Field(..., min_length=6, max_length=6, description="6位密码")


class MessageResponse(BaseModel):
    """消息响应"""
    message: str = Field(description="操作消息")
