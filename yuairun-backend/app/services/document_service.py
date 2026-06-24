"""文档上传/删除业务逻辑"""

import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.session import get_session
from app.db.models.knowledge_base import KnowledgeBaseModel
from app.db.models.knowledge_document import KnowledgeDocumentModel
from app.models.knowledge import KnowledgeDocumentInfo
from app.services.document_processor import process_document
from app.services.vector_service import delete_document_chunks

logger = logging.getLogger(__name__)

MAX_DOCS_PER_KB = 50
UPLOAD_DIR = "uploads/knowledge"


def _generate_id(prefix: str = "kd") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


async def upload_document(
    user_id: str,
    kb_id: str,
    filename: str,
    file_content: bytes,
) -> Optional[str]:
    """上传文档并启动异步处理"""
    async with get_session() as session:
        # 检查知识库是否存在
        kb_stmt = select(KnowledgeBaseModel).where(KnowledgeBaseModel.id == kb_id)
        kb_result = await session.execute(kb_stmt)
        kb = kb_result.scalar_one_or_none()
        if kb is None:
            logger.warning("知识库不存在: %s", kb_id)
            return None
        
        # 检查文档数量限制
        count_stmt = select(func.count()).select_from(KnowledgeDocumentModel).where(
            KnowledgeDocumentModel.kb_id == kb_id
        )
        count_result = await session.execute(count_stmt)
        doc_count = count_result.scalar()
        if doc_count and doc_count >= MAX_DOCS_PER_KB:
            logger.warning("知识库文档数已达上限: %s", kb_id)
            return None
        
        ext = os.path.splitext(filename)[1].lower()
        doc_id = _generate_id("kd")
        file_path = os.path.join(UPLOAD_DIR, kb_id, f"{doc_id}{ext}")
        
        # 确保上传目录存在
        abs_dir = os.path.join(get_settings().knowledge_base_dir, "..", file_path)
        abs_dir = os.path.abspath(abs_dir)
        os.makedirs(os.path.dirname(abs_dir), exist_ok=True)
        
        # 保存文件
        with open(abs_dir, "wb") as f:
            f.write(file_content)
        
        now = datetime.now(timezone.utc)
        doc = KnowledgeDocumentModel(
            id=doc_id,
            kb_id=kb_id,
            user_id=user_id,
            filename=filename,
            file_type=ext.lstrip("."),
            file_size=len(file_content),
            file_path=file_path,
            status="pending",
            created_at=now,
            updated_at=now,
        )
        session.add(doc)
        
        # 更新知识库文档计数
        kb.doc_count = (kb.doc_count or 0) + 1
        kb.updated_at = now
        
        await session.commit()
        await session.refresh(doc)
        
        # 异步处理文档
        chunk_count = await process_document(
            file_path=abs_dir,
            kb_id=kb_id,
            doc_id=doc_id,
            filename=filename,
        )
        
        # 更新处理结果
        async with get_session() as session:
            stmt = select(KnowledgeDocumentModel).where(KnowledgeDocumentModel.id == doc_id)
            result = await session.execute(stmt)
            doc_model = result.scalar_one_or_none()
            if doc_model:
                doc_model.status = "ready" if chunk_count > 0 else "failed"
                doc_model.chunk_count = chunk_count
                if chunk_count == 0:
                    doc_model.error_msg = "文档解析后为空或解析失败"
                doc_model.updated_at = datetime.now(timezone.utc)
                
                # 更新知识库分块计数
                kb_stmt = select(KnowledgeBaseModel).where(KnowledgeBaseModel.id == kb_id)
                kb_result = await session.execute(kb_stmt)
                kb_model = kb_result.scalar_one_or_none()
                if kb_model:
                    kb_model.chunk_count = (kb_model.chunk_count or 0) + chunk_count
                
                await session.commit()
        
        return doc_id


async def get_kb_documents(kb_id: str) -> list[KnowledgeDocumentInfo]:
    """获取知识库文档列表"""
    async with get_session() as session:
        stmt = select(KnowledgeDocumentModel).where(
            KnowledgeDocumentModel.kb_id == kb_id
        ).order_by(KnowledgeDocumentModel.created_at.desc())
        
        result = await session.execute(stmt)
        models = result.scalars().all()
        
        return [
            KnowledgeDocumentInfo(
                id=m.id,
                kb_id=m.kb_id,
                filename=m.filename,
                file_type=m.file_type,
                file_size=m.file_size or 0,
                page_count=m.page_count,
                char_count=m.char_count or 0,
                chunk_count=m.chunk_count or 0,
                status=m.status or "pending",
                error_msg=m.error_msg,
                created_at=m.created_at,
            )
            for m in models
        ]


async def delete_document(doc_id: str, user_id: str) -> tuple[bool, Optional[str]]:
    """删除文档"""
    async with get_session() as session:
        stmt = select(KnowledgeDocumentModel).where(KnowledgeDocumentModel.id == doc_id)
        result = await session.execute(stmt)
        doc = result.scalar_one_or_none()
        
        if doc is None:
            return False, "文档不存在"
        
        if doc.user_id != user_id:
            return False, "无权删除此文档"
        
        # 删除 ChromaDB 向量
        await delete_document_chunks(doc_id)
        
        # 删除文件
        settings = get_settings()
        abs_path = os.path.abspath(
            os.path.join(settings.knowledge_base_dir, "..", doc.file_path)
        )
        if os.path.exists(abs_path):
            os.remove(abs_path)
        
        # 更新知识库统计
        kb_stmt = select(KnowledgeBaseModel).where(KnowledgeBaseModel.id == doc.kb_id)
        kb_result = await session.execute(kb_stmt)
        kb = kb_result.scalar_one_or_none()
        if kb:
            kb.doc_count = max(0, (kb.doc_count or 0) - 1)
            kb.chunk_count = max(0, (kb.chunk_count or 0) - (doc.chunk_count or 0))
        
        # 删除数据库记录
        await session.delete(doc)
        await session.commit()
        
        return True, None
