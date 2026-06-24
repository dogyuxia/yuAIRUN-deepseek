"""知识库相关的 Pydantic 数据模型"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ============================================================
# 知识库
# ============================================================

class KnowledgeBaseInfo(BaseModel):
    """知识库信息"""
    id: str = Field(description="知识库ID")
    name: str = Field(description="知识库名称")
    description: str = Field(default="", description="知识库描述")
    isSystem: bool = Field(default=False, validation_alias="is_system", description="是否为系统内置")
    docCount: int = Field(default=0, validation_alias="doc_count", description="文档数量")
    chunkCount: int = Field(default=0, validation_alias="chunk_count", description="分块数量")
    createdAt: datetime = Field(validation_alias="created_at", description="创建时间")
    updatedAt: datetime = Field(validation_alias="updated_at", description="更新时间")


class CreateKnowledgeBaseRequest(BaseModel):
    """创建知识库请求"""
    name: str = Field(min_length=1, max_length=128, description="知识库名称")
    description: str = Field(default="", max_length=512, description="知识库描述")


class KnowledgeBaseListResponse(BaseModel):
    """知识库列表响应"""
    success: bool = True
    data: list[KnowledgeBaseInfo] = Field(default=[])
    error: str | None = None


class KnowledgeBaseDeleteResponse(BaseModel):
    """删除知识库响应"""
    success: bool = True
    error: str | None = None


# ============================================================
# 文档
# ============================================================

class KnowledgeDocumentInfo(BaseModel):
    """文档信息"""
    id: str = Field(description="文档ID")
    kbId: str = Field(validation_alias="kb_id", description="所属知识库ID")
    filename: str = Field(description="原始文件名")
    fileType: str = Field(validation_alias="file_type", description="文件类型")
    fileSize: int = Field(default=0, validation_alias="file_size", description="文件大小")
    pageCount: int | None = Field(default=None, validation_alias="page_count", description="页数")
    charCount: int = Field(default=0, validation_alias="char_count", description="字符数")
    chunkCount: int = Field(default=0, validation_alias="chunk_count", description="分块数")
    status: str = Field(default="pending", description="状态")
    errorMsg: str | None = Field(default=None, validation_alias="error_msg", description="错误信息")
    createdAt: datetime = Field(validation_alias="created_at", description="上传时间")


class KnowledgeDocumentListResponse(BaseModel):
    """文档列表响应"""
    success: bool = True
    data: list[KnowledgeDocumentInfo] = Field(default=[])
    error: str | None = None


class DocumentUploadResponse(BaseModel):
    """文档上传响应"""
    success: bool = True
    documentId: str = Field(validation_alias="document_id", description="文档ID")
    error: str | None = None


class DocumentDeleteResponse(BaseModel):
    """删除文档响应"""
    success: bool = True
    error: str | None = None
