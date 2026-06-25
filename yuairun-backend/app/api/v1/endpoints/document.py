"""文档上传与管理 API 路由"""

import logging
import os

from fastapi import APIRouter, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse

from app.models.knowledge import (
    KnowledgeDocumentListResponse,
    KnowledgeDocumentInfo,
    DocumentUploadResponse,
    DocumentDeleteResponse,
)
from app.services.document_service import (
    get_kb_documents,
    upload_document,
    delete_document,
)
from app.utils.auth import get_current_user_id

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])

# 允许的文件类型
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB


@router.post("/base/{kb_id}/documents", response_model=DocumentUploadResponse)
async def upload_doc(
    kb_id: str,
    file: UploadFile,
    filename: str = Form(None),
    user_id: str = Depends(get_current_user_id),
):
    """上传文档到知识库"""
    # 使用前端传来的原始文件名（避免 WeChat 临时路径乱码）
    original_filename = filename or file.filename or "unnamed"
    
    # 校验文件类型
    ext = os.path.splitext(original_filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return DocumentUploadResponse(
            success=False,
            error=f"不支持的文件格式，仅支持 {', '.join(ALLOWED_EXTENSIONS)}",
        )
    
    # 读取文件内容
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        return DocumentUploadResponse(
            success=False,
            error="文件大小不能超过 20MB",
        )
    
    doc_id = await upload_document(
        user_id=user_id,
        kb_id=kb_id,
        filename=original_filename,
        file_content=content,
    )
    
    if doc_id is None:
        return DocumentUploadResponse(success=False, error="文档上传失败")
    
    return DocumentUploadResponse(success=True, document_id=doc_id)


@router.get("/base/{kb_id}/documents", response_model=KnowledgeDocumentListResponse)
async def list_docs(
    kb_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """获取知识库文档列表"""
    docs = await get_kb_documents(kb_id)
    return KnowledgeDocumentListResponse(data=docs)


@router.delete("/document/{doc_id}", response_model=DocumentDeleteResponse)
async def delete_doc(
    doc_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """删除文档"""
    success, error = await delete_document(doc_id, user_id)
    if not success:
        return DocumentDeleteResponse(success=False, error=error)
    return DocumentDeleteResponse(success=True)
