"""知识库管理 API 路由"""

import logging

from fastapi import APIRouter, Depends

from app.models.knowledge import (
    CreateKnowledgeBaseRequest,
    KnowledgeBaseListResponse,
    KnowledgeBaseInfo,
    KnowledgeBaseDeleteResponse,
)
from app.services.knowledge_service import (
    get_user_knowledge_bases,
    create_knowledge_base,
    delete_knowledge_base,
)
from app.utils.auth import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


@router.post("/base")
async def create_base(
    request: CreateKnowledgeBaseRequest,
    user_id: str = Depends(get_current_user_id),
):
    """创建知识库"""
    try:
        kb = await create_knowledge_base(user_id, request.name, request.description)
        return {"success": True, "data": kb.model_dump()}
    except ValueError as e:
        return {"success": False, "error": str(e)}
    except Exception as e:
        return {"success": False, "error": f"创建失败: {str(e)}"}


@router.get("/bases", response_model=KnowledgeBaseListResponse)
async def list_bases(user_id: str = Depends(get_current_user_id)):
    """获取知识库列表（含系统知识库）"""
    bases = await get_user_knowledge_bases(user_id)
    return KnowledgeBaseListResponse(data=bases)


@router.delete("/base/{kb_id}", response_model=KnowledgeBaseDeleteResponse)
async def delete_base(
    kb_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """删除知识库"""
    success, error = await delete_knowledge_base(kb_id, user_id)
    if not success:
        return KnowledgeBaseDeleteResponse(success=False, error=error)
    return KnowledgeBaseDeleteResponse(success=True)
