"""知识库业务逻辑"""

import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.session import DbSession

get_session = DbSession
from app.db.models.knowledge_base import KnowledgeBaseModel
from app.db.models.knowledge_document import KnowledgeDocumentModel
from app.models.knowledge import KnowledgeBaseInfo
from app.services.vector_service import delete_kb_chunks, add_document_chunks
from app.services.document_processor import _fallback_extract_text

logger = logging.getLogger(__name__)

SYSTEM_USER_ID = "system"
MAX_KB_PER_USER = 10
SYSTEM_KB_ID = "kb_system_ai_agent"


def _generate_id(prefix: str = "kb") -> str:
    """生成唯一 ID"""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


async def get_user_knowledge_bases(user_id: str) -> list[KnowledgeBaseInfo]:
    """获取用户的所有知识库（含系统知识库）"""
    async with get_session() as session:
        stmt = select(KnowledgeBaseModel).where(
            (KnowledgeBaseModel.user_id == user_id) |
            (KnowledgeBaseModel.user_id == SYSTEM_USER_ID)
        ).order_by(KnowledgeBaseModel.updated_at.desc())
        
        result = await session.execute(stmt)
        models = result.scalars().all()
        
        return [
            KnowledgeBaseInfo(
                id=m.id,
                name=m.name,
                description=m.description or "",
                is_system=m.is_system or False,
                doc_count=m.doc_count or 0,
                chunk_count=m.chunk_count or 0,
                created_at=m.created_at,
                updated_at=m.updated_at,
            )
            for m in models
        ]


async def create_knowledge_base(
    user_id: str,
    name: str,
    description: str = "",
) -> KnowledgeBaseInfo:
    """创建知识库"""
    async with get_session() as session:
        # 检查数量限制
        count_stmt = select(KnowledgeBaseModel).where(
            KnowledgeBaseModel.user_id == user_id
        )
        result = await session.execute(count_stmt)
        existing = result.scalars().all()
        if len(existing) >= MAX_KB_PER_USER:
            raise ValueError(f"知识库数量已达上限（{MAX_KB_PER_USER}个）")
        
        now = datetime.now(timezone.utc)
        kb = KnowledgeBaseModel(
            id=_generate_id("kb"),
            user_id=user_id,
            name=name,
            description=description,
            is_system=False,
            created_at=now,
            updated_at=now,
        )
        session.add(kb)
        await session.commit()
        await session.refresh(kb)
        
        return KnowledgeBaseInfo(
            id=kb.id,
            name=kb.name,
            description=kb.description or "",
            is_system=False,
            doc_count=0,
            chunk_count=0,
            created_at=kb.created_at,
            updated_at=kb.updated_at,
        )


async def delete_knowledge_base(kb_id: str, user_id: str) -> tuple[bool, Optional[str]]:
    """删除知识库"""
    async with get_session() as session:
        stmt = select(KnowledgeBaseModel).where(KnowledgeBaseModel.id == kb_id)
        result = await session.execute(stmt)
        kb = result.scalar_one_or_none()
        
        if kb is None:
            return False, "知识库不存在"
        
        if kb.is_system:
            return False, "不能删除系统知识库"
        
        if kb.user_id != user_id:
            return False, "无权删除此知识库"
        
        # 删除 ChromaDB 中的向量
        await delete_kb_chunks(kb_id)
        
        # 删除数据库记录
        await session.delete(kb)
        await session.commit()
        
        return True, None


async def _index_system_markdown_files():
    """读取并索引 knowledge_base/default/ 下的所有 markdown 文件到系统知识库"""
    # 计算项目根目录 (yuairun-backend/)
    backend_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    kb_base_dir = os.path.join(backend_root, "knowledge_base", "default")

    if not os.path.isdir(kb_base_dir):
        logger.warning("系统知识包目录不存在: %s", kb_base_dir)
        return

    async with get_session() as session:
        # 检查是否已有文档索引
        stmt = select(KnowledgeDocumentModel).where(
            KnowledgeDocumentModel.kb_id == SYSTEM_KB_ID,
            KnowledgeDocumentModel.user_id == SYSTEM_USER_ID,
        ).limit(1)
        existing = await session.execute(stmt)
        if existing.scalar_one_or_none():
            logger.info("系统知识包文档已索引，跳过")
            return

    # 检查 ChromaDB 是否可用（无需 BGE-M3 模型，原生 ChromaDB 使用内置 embedding）
    try:
        from app.services.vector_service import get_collection
        collection = get_collection()
        if collection is None:
            logger.warning("⚠️ ChromaDB 不可用，跳过系统知识包索引")
            return
    except Exception:
        logger.warning("⚠️ ChromaDB 未就绪，跳过系统知识包索引")
        return

    total_docs = 0
    total_chunks = 0

    for root, dirs, files in os.walk(kb_base_dir):
        for filename in sorted(files):
            if not filename.endswith((".md", ".txt")):
                continue

            file_path = os.path.join(root, filename)
            rel_dir = os.path.relpath(root, kb_base_dir)
            kb_filename = f"{rel_dir}/{filename}" if rel_dir != "." else filename

            try:
                # 读取并分块
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()

                if not content.strip():
                    logger.warning("系统知识包文件为空: %s", kb_filename)
                    continue

                chunks = await _fallback_extract_text(file_path)
                if not chunks:
                    logger.warning("系统知识包文件解析失败: %s", kb_filename)
                    continue

                # 生成文档 ID
                doc_id = f"kd_sys_{uuid.uuid4().hex[:12]}"

                # 存入 ChromaDB
                chunk_count = await add_document_chunks(
                    kb_id=SYSTEM_KB_ID,
                    doc_id=doc_id,
                    filename=kb_filename,
                    chunks=chunks,
                )

                if chunk_count == 0:
                    continue

                # 创建文档记录
                async with get_session() as session:
                    now = datetime.now(timezone.utc)
                    doc = KnowledgeDocumentModel(
                        id=doc_id,
                        kb_id=SYSTEM_KB_ID,
                        user_id=SYSTEM_USER_ID,
                        filename=kb_filename,
                        file_type="md",
                        file_size=len(content.encode("utf-8")),
                        file_path=file_path,
                        char_count=len(content),
                        chunk_count=chunk_count,
                        status="ready",
                        created_at=now,
                        updated_at=now,
                    )
                    session.add(doc)

                    # 更新知识库统计
                    kb_stmt = select(KnowledgeBaseModel).where(
                        KnowledgeBaseModel.id == SYSTEM_KB_ID
                    )
                    kb_result = await session.execute(kb_stmt)
                    kb = kb_result.scalar_one_or_none()
                    if kb:
                        kb.doc_count = (kb.doc_count or 0) + 1
                        kb.chunk_count = (kb.chunk_count or 0) + chunk_count
                        kb.updated_at = now

                    await session.commit()

                total_docs += 1
                total_chunks += chunk_count
                logger.info("  ✅ 已索引: %s (%d 块)", kb_filename, chunk_count)

            except Exception as e:
                logger.error("系统知识包文件索引失败 %s: %s", kb_filename, e)

    logger.info("✅ 系统知识包索引完成: %d 个文档, %d 个分块", total_docs, total_chunks)


async def seed_system_knowledge_bases():
    """初始化系统知识库（应用启动时调用）"""
    async with get_session() as session:
        # 1. 先确保系统用户存在（否则外键约束会失败）
        from app.db.models.user import UserModel
        sys_user_stmt = select(UserModel).where(UserModel.id == SYSTEM_USER_ID)
        sys_user_result = await session.execute(sys_user_stmt)
        sys_user = sys_user_result.scalar_one_or_none()

        if sys_user is None:
            now = datetime.now(timezone.utc)
            sys_user = UserModel(
                id=SYSTEM_USER_ID,
                openid=SYSTEM_USER_ID,
                nickname="系统",
                avatar_url="",
                xp=0,
                level=1,
                last_login_at=now,
                created_at=now,
                updated_at=now,
            )
            session.add(sys_user)
            await session.commit()
            logger.info("✅ 系统用户已创建 (id=%s)", SYSTEM_USER_ID)
        else:
            logger.info("系统用户已存在")

        # 2. 创建系统知识库
        stmt = select(KnowledgeBaseModel).where(
            KnowledgeBaseModel.is_system == True
        )
        result = await session.execute(stmt)
        existing = result.scalars().all()

        if not existing:
            now = datetime.now(timezone.utc)
            kb = KnowledgeBaseModel(
                id=SYSTEM_KB_ID,
                user_id=SYSTEM_USER_ID,
                name="AI Agent 知识库",
                description="系统内置的 AI Agent 相关知识库，涵盖 Agent 基础概念、LangChain 框架、设计模式等",
                is_system=True,
                created_at=now,
                updated_at=now,
            )
            session.add(kb)
            await session.commit()
            logger.info("✅ 系统知识库 'AI Agent 知识库' 已创建")
        else:
            logger.info("系统知识库已存在，继续索引文档...")

    # 索引系统知识包文件（每次都尝试，因为可能有新文件）
    await _index_system_markdown_files()
