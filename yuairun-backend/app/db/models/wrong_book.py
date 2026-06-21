"""WrongBook ORM 模型"""

from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, DateTime, JSON, SmallInteger, ForeignKey, Index

from app.db.session import Base


class WrongBookModel(Base):
    """错题本表"""
    __tablename__ = "wrong_book"

    id = Column(String(32), primary_key=True, comment="记录ID，格式 wb_xxx")
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False, comment="用户ID")
    history_id = Column(String(32), ForeignKey("quiz_history.id", ondelete="CASCADE"), nullable=False, comment="来源闯关记录ID")
    question = Column(JSON, nullable=False, comment="完整题目对象")
    user_answer = Column(String(256), nullable=False, comment="用户当时的选择")
    correct_answer = Column(String(256), nullable=False, comment="正确答案")
    subject = Column(String(64), nullable=False, comment="学科")
    topic = Column(String(256), nullable=False, comment="知识点")
    wrong_count = Column(Integer, nullable=False, default=1, comment="答错次数（累计）")
    last_wrong_at = Column(DateTime, nullable=False, comment="最近一次答错时间")
    is_mastered = Column(SmallInteger, nullable=False, default=0, comment="是否已掌握")
    created_at = Column(DateTime, nullable=False, comment="首次加入错题本时间")
    updated_at = Column(DateTime, nullable=False, comment="更新时间")

    __table_args__ = (
        Index("idx_user_subject", "user_id", "subject"),
        Index("idx_user_mastered", "user_id", "is_mastered"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "question": self.question,
            "userAnswer": self.user_answer,
            "correctAnswer": self.correct_answer,
            "subject": self.subject,
            "topic": self.topic,
            "wrongCount": self.wrong_count,
            "lastWrongAt": self.last_wrong_at.isoformat() if self.last_wrong_at else None,
            "isMastered": bool(self.is_mastered),
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }
