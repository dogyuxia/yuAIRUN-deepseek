"""QuizAnswer ORM 模型"""

from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, DateTime, JSON, SmallInteger, ForeignKey, Index

from app.db.session import Base


class QuizAnswerModel(Base):
    """答题详情表"""
    __tablename__ = "quiz_answers"

    id = Column(String(32), primary_key=True, comment="记录ID，格式 qa_xxx")
    history_id = Column(String(32), ForeignKey("quiz_history.id", ondelete="CASCADE"), nullable=False, comment="关联的闯关记录ID")
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False, comment="用户ID")
    question = Column(JSON, nullable=False, comment="完整题目对象（含选项、答案、解析）")
    user_answer = Column(String(256), nullable=False, comment="用户的答案")
    is_correct = Column(SmallInteger, nullable=False, comment="是否正确")
    created_at = Column(DateTime, nullable=False, comment="创建时间")

    __table_args__ = (
        Index("idx_history", "history_id"),
        Index("idx_user_correct", "user_id", "is_correct"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "historyId": self.history_id,
            "question": self.question,
            "userAnswer": self.user_answer,
            "isCorrect": bool(self.is_correct),
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }
