"""QuizHistory ORM 模型"""

from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, DateTime, DECIMAL, ForeignKey, Index

from app.db.session import Base


class QuizHistoryModel(Base):
    """闯关历史表"""
    __tablename__ = "quiz_history"

    id = Column(String(32), primary_key=True, comment="记录ID，格式 h_xxx")
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False, comment="用户ID")
    subject = Column(String(64), nullable=False, comment="学科")
    topic = Column(String(256), nullable=False, comment="知识点")
    question_count = Column(Integer, nullable=False, comment="总题数")
    correct_count = Column(Integer, nullable=False, comment="正确数")
    accuracy = Column(DECIMAL(4, 3), nullable=False, comment="正确率 0.000~1.000")
    duration = Column(Integer, nullable=False, default=0, comment="答题用时（秒）")
    xp_earned = Column(Integer, nullable=False, default=0, comment="获得经验值")
    created_at = Column(DateTime, nullable=False, comment="创建时间")

    __table_args__ = (
        Index("idx_user_created", "user_id", "created_at"),
        Index("idx_user_subject", "user_id", "subject"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "subject": self.subject,
            "topic": self.topic,
            "questionCount": self.question_count,
            "correctCount": self.correct_count,
            "accuracy": float(self.accuracy),
            "duration": self.duration,
            "xpEarned": self.xp_earned,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }
