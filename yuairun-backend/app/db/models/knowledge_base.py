"""知识库 ORM 模型"""

from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, Boolean

from app.db.session import Base


class KnowledgeBaseModel(Base):
    """知识库表"""
    __tablename__ = "knowledge_bases"

    id = Column(String(32), primary_key=True, comment="知识库ID，格式 kb_xxx")
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False, comment="所属用户ID")
    name = Column(String(128), nullable=False, comment="知识库名称")
    description = Column(Text, default="", comment="知识库描述")
    is_system = Column(Boolean, default=False, comment="是否为系统内置知识库")
    doc_count = Column(Integer, default=0, comment="文档数量")
    chunk_count = Column(Integer, default=0, comment="分块数量")
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), comment="创建时间")
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), comment="更新时间")
