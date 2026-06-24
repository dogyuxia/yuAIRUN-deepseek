"""知识库文档 ORM 模型"""

from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey

from app.db.session import Base


class KnowledgeDocumentModel(Base):
    """知识库文档表"""
    __tablename__ = "knowledge_documents"

    id = Column(String(32), primary_key=True, comment="文档ID，格式 kd_xxx")
    kb_id = Column(String(32), ForeignKey("knowledge_bases.id", ondelete="CASCADE"), nullable=False, comment="所属知识库ID")
    user_id = Column(String(32), ForeignKey("users.id"), nullable=False, comment="上传用户ID")
    filename = Column(String(256), nullable=False, comment="原始文件名")
    file_type = Column(String(16), nullable=False, comment="文件类型: pdf/docx/txt/md")
    file_size = Column(Integer, default=0, comment="文件大小（字节）")
    file_path = Column(String(512), nullable=False, comment="文件存储路径")
    page_count = Column(Integer, nullable=True, comment="页数（PDF）")
    char_count = Column(Integer, default=0, comment="字符数")
    chunk_count = Column(Integer, default=0, comment="分块数")
    status = Column(String(16), default="pending", comment="状态: pending/processing/ready/failed")
    error_msg = Column(Text, nullable=True, comment="处理失败原因")
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), comment="上传时间")
    updated_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), comment="更新时间")
