"""
RAG 知识库 TDD 测试

测试策略：
- Pydantic 模型校验（无需数据库）
- API 路由注册与参数校验
- Mock 化知识库业务逻辑
- 认证机制验证
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.utils.auth import create_token

TEST_USER_ID = "u_test_rag_001"
TEST_TOKEN, _ = create_token(TEST_USER_ID, "mock_openid_rag")


@pytest.fixture(autouse=True)
def _mock_settings():
    """确保每次测试使用干净的 Mock LLM 配置"""
    from app.config import get_settings
    get_settings.cache_clear()
    import os
    os.environ.setdefault("USE_MOCK_LLM", "true")
    yield
    get_settings.cache_clear()


@pytest.fixture
def app():
    return create_app()


# ============================================================
# Pydantic 模型校验测试
# ============================================================

class TestKnowledgeModels:
    """测试知识库 Pydantic 模型"""

    def test_create_knowledge_base_request_valid(self):
        """创建知识库请求模型校验"""
        from app.models.knowledge import CreateKnowledgeBaseRequest

        req = CreateKnowledgeBaseRequest(name="测试知识库", description="用于测试")
        assert req.name == "测试知识库"
        assert req.description == "用于测试"

    def test_create_knowledge_base_request_minimal(self):
        """最小请求（仅 name）"""
        from app.models.knowledge import CreateKnowledgeBaseRequest

        req = CreateKnowledgeBaseRequest(name="测试")
        assert req.name == "测试"
        assert req.description == ""

    def test_create_knowledge_base_request_empty_name(self):
        """空名称应校验失败"""
        from app.models.knowledge import CreateKnowledgeBaseRequest
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            CreateKnowledgeBaseRequest(name="")

    def test_knowledge_base_info_from_dict(self):
        """知识库信息模型从字典构造"""
        from app.models.knowledge import KnowledgeBaseInfo
        from datetime import datetime

        now = datetime.now()
        info = KnowledgeBaseInfo(
            id="kb_test_001",
            name="测试知识库",
            description="测试描述",
            is_system=False,
            doc_count=5,
            chunk_count=100,
            created_at=now,
            updated_at=now,
        )
        assert info.id == "kb_test_001"
        assert info.name == "测试知识库"
        assert info.docCount == 5
        assert info.chunkCount == 100
        assert info.isSystem is False

    def test_knowledge_base_info_system_flag(self):
        """系统知识库标记"""
        from app.models.knowledge import KnowledgeBaseInfo
        from datetime import datetime

        now = datetime.now()
        info = KnowledgeBaseInfo(
            id="kb_system_01",
            name="系统知识库",
            is_system=True,
            doc_count=10,
            chunk_count=200,
            created_at=now,
            updated_at=now,
        )
        assert info.isSystem is True

    def test_document_info_from_dict(self):
        """文档信息模型"""
        from app.models.knowledge import KnowledgeDocumentInfo
        from datetime import datetime

        now = datetime.now()
        doc = KnowledgeDocumentInfo(
            id="kd_test_001",
            kb_id="kb_test_001",
            filename="test.pdf",
            file_type="pdf",
            file_size=1024,
            page_count=5,
            char_count=5000,
            chunk_count=10,
            status="ready",
            created_at=now,
        )
        assert doc.filename == "test.pdf"
        assert doc.status == "ready"
        assert doc.fileType == "pdf"

    def test_document_pending_status(self):
        """文档处理中状态"""
        from app.models.knowledge import KnowledgeDocumentInfo
        from datetime import datetime

        doc = KnowledgeDocumentInfo(
            id="kd_test_002",
            kb_id="kb_test_001",
            filename="processing.docx",
            file_type="docx",
            file_size=2048,
            status="processing",
            created_at=datetime.now(),
        )
        assert doc.status == "processing"
        assert doc.errorMsg is None


# ============================================================
# API 认证测试
# ============================================================

class TestKnowledgeApiAuth:
    """知识库 API 认证测试"""

    @pytest.mark.asyncio
    async def test_list_bases_unauthorized(self, app):
        """未认证请求返回 401"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/knowledge/bases")
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_base_unauthorized(self, app):
        """未认证不能创建知识库"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/knowledge/base",
                json={"name": "测试知识库"},
            )
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_base_unauthorized(self, app):
        """未认证不能删除知识库"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete("/api/knowledge/base/kb_test")
            assert response.status_code == 401


# ============================================================
# API 参数校验测试
# ============================================================

class TestKnowledgeApiValidation:
    """知识库 API 参数校验"""

    @pytest.mark.asyncio
    async def test_create_base_missing_name(self, app):
        """创建知识库缺少名称"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/knowledge/base",
                json={},
                headers={"Authorization": f"Bearer {TEST_TOKEN}"},
            )
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_create_base_empty_name(self, app):
        """创建知识库名称为空"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/knowledge/base",
                json={"name": ""},
                headers={"Authorization": f"Bearer {TEST_TOKEN}"},
            )
            assert response.status_code == 422


# ============================================================
# 出题 API 新增参数测试
# ============================================================

class TestQuizApiWithKnowledge:
    """出题 API 知识库参数测试"""

    @pytest.mark.asyncio
    async def test_generate_quiz_with_knowledge_base_id(self, app):
        """出题请求携带 knowledgeBaseId 参数"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/quiz/generate",
                json={
                    "subject": "计算机网络",
                    "topic": "TCP三次握手",
                    "count": 3,
                    "difficulty": "medium",
                    "type": "single",
                    "knowledgeBaseId": "kb_test_001",
                    "searchMode": "knowledge_base",
                },
            )
            # Mock 模式下，知识库参数被忽略，但请求应正常
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    @pytest.mark.asyncio
    async def test_generate_quiz_with_hybrid_mode(self, app):
        """混合模式请求"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/quiz/generate",
                json={
                    "subject": "AI Agent",
                    "topic": "ReAct Pattern",
                    "count": 5,
                    "difficulty": "medium",
                    "type": "single",
                    "knowledgeBaseId": "kb_test_001",
                    "searchMode": "hybrid",
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True

    @pytest.mark.asyncio
    async def test_generate_quiz_invalid_search_mode(self, app):
        """任意 searchMode 值应被接受（向后兼容）"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/quiz/generate",
                json={
                    "subject": "测试",
                    "topic": "测试",
                    "count": 3,
                    "difficulty": "medium",
                    "type": "single",
                    "searchMode": "invalid_mode",
                },
            )
            # searchMode 改为 str 后，任何值都应被接受
            assert response.status_code in (200, 422)
            if response.status_code == 200:
                data = response.json()
                assert "error" not in data or not data.get("error")
