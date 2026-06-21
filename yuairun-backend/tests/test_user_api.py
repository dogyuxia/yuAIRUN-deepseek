"""
用户系统 TDD 测试

测试策略：
- 使用 pytest 和 httpx 的 AsyncClient 测试 API 端点
- 通过 mock 跳过数据库依赖，确保核心逻辑正确
- 测试认证机制、参数校验
- 验证现有核心功能不受影响
"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.utils.auth import create_token


@pytest.fixture
def app():
    """创建测试用应用实例"""
    return create_app()


# 测试 Token（用于认证）
TEST_USER_ID = "u_test_001"
TEST_OPENID = "mock_openid_test"
TEST_TOKEN, TEST_EXPIRES = create_token(TEST_USER_ID, TEST_OPENID)


# ============================================================
# P0: 登录认证 - JWT 工具函数直接测试
# ============================================================

class TestJwtUtils:
    """测试 JWT 工具函数"""

    def test_create_and_verify_token(self):
        """签发和验证 Token 应正常"""
        from app.utils.auth import create_token, verify_token

        token, expires = create_token("u_test", "openid_test")
        assert len(token) > 20
        assert expires > 0

        payload = verify_token(token)
        assert payload["sub"] == "u_test"
        assert payload["openid"] == "openid_test"

    def test_invalid_token_raises(self):
        """无效 Token 应抛出异常"""
        from app.utils.auth import verify_token
        from fastapi import HTTPException

        try:
            verify_token("invalid_token")
            assert False, "应抛出异常"
        except HTTPException as e:
            assert e.status_code == 401


# ============================================================
# P1: 个人中心 - 认证检查
# ============================================================

class TestProfileAuth:
    """测试认证保护"""

    @pytest.mark.asyncio
    async def test_profile_unauthorized(self, app):
        """未认证请求应返回 401"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/user/profile")
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_update_profile_unauthorized(self, app):
        """未认证不能更新信息"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put(
                "/api/user/profile",
                json={"nickname": "新名字"},
            )
            assert response.status_code == 401


# ============================================================
# P2: 闯关历史 - 认证检查
# ============================================================

class TestHistoryAuth:
    """测试闯关历史认证"""

    @pytest.mark.asyncio
    async def test_history_list_unauthorized(self, app):
        """未认证请求历史列表应返回 401"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/user/history")
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_history_detail_unauthorized(self, app):
        """未认证请求历史详情应返回 401"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/user/history/h_001")
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_history_sync_unauthorized(self, app):
        """未认证不能同步闯关记录"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/user/history/sync",
                json={"records": []},
            )
            assert response.status_code == 401


# ============================================================
# P2: 错题本 - 认证检查
# ============================================================

class TestWrongBookAuth:
    """测试错题本认证"""

    @pytest.mark.asyncio
    async def test_wrong_book_unauthorized(self, app):
        """未认证请求错题本应返回 401"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/user/wrong-book")
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_wrong_book_sync_unauthorized(self, app):
        """未认证不能同步错题"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/user/wrong-book/sync",
                json={"items": []},
            )
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_wrong_book_master_unauthorized(self, app):
        """未认证不能标记掌握"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.put("/api/user/wrong-book/wb_001/master")
            assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_wrong_book_delete_unauthorized(self, app):
        """未认证不能删除错题"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.delete("/api/user/wrong-book/wb_001")
            assert response.status_code == 401


# ============================================================
# XP 和等级计算单元测试
# ============================================================

class TestXpCalculation:
    """测试 XP 计算逻辑"""

    def test_calculate_level(self):
        """测试等级计算"""
        from app.services.user_service import calculate_level

        assert calculate_level(0) == 1
        assert calculate_level(50) == 1
        assert calculate_level(100) == 2
        assert calculate_level(200) == 2
        assert calculate_level(300) == 3
        assert calculate_level(600) == 4
        assert calculate_level(1000) == 5
        assert calculate_level(2000) == 6
        assert calculate_level(3000) == 6

    def test_get_level_title(self):
        """测试等级称号"""
        from app.services.user_service import get_level_title

        assert get_level_title(1) == "初学者"
        assert get_level_title(2) == "学徒"
        assert get_level_title(3) == "探究者"
        assert get_level_title(4) == "学者"
        assert get_level_title(5) == "大师"
        assert get_level_title(6) == "传奇"
        assert get_level_title(7) == "传奇"

    def test_calculate_xp_earned(self):
        """测试 XP 计算"""
        from app.services.user_service import calculate_xp_earned

        # 5题全对，首次闯关
        xp = calculate_xp_earned(5, 5, is_first_quiz=True)
        assert xp == 5 * 10 + (5 - 1) * 5 + 50 + 20  # 50 + 20 + 50 + 20 = 140
        assert xp == 140

        # 3题全对，非首次
        xp = calculate_xp_earned(3, 3, is_first_quiz=False)
        assert xp == 3 * 10 + (3 - 1) * 5 + 20  # 30 + 10 + 20 = 60
        assert xp == 60

        # 5对3，非首次
        xp = calculate_xp_earned(3, 5, is_first_quiz=False)
        assert xp == 3 * 10 + (3 - 1) * 5  # 30 + 10 = 40
        assert xp == 40

    def test_generate_id(self):
        """测试 ID 生成"""
        from app.services.user_service import generate_id

        uid = generate_id("u")
        assert uid.startswith("u_")
        assert len(uid) > 10

        hid = generate_id("h")
        assert hid.startswith("h_")


# ============================================================
# 扩展测试：验证现有核心功能不受影响
# ============================================================

class TestExistingCoreFunctions:
    """验证现有核心功能不受影响"""

    @pytest.mark.asyncio
    async def test_health_check_still_works(self, app):
        """健康检查应仍然正常工作"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"

    @pytest.mark.asyncio
    async def test_quiz_generate_still_works(self, app):
        """出题接口应仍然正常工作"""
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
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]["questions"]) == 3

    @pytest.mark.asyncio
    async def test_quiz_analyze_still_works(self, app):
        """分析报告接口应仍然正常工作"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 先出题
            gen_resp = await client.post(
                "/api/quiz/generate",
                json={
                    "subject": "测试",
                    "topic": "测试",
                    "count": 2,
                    "difficulty": "medium",
                    "type": "single",
                },
            )
            quiz_data = gen_resp.json()["data"]

            # 分析
            user_answers = {}
            for q in quiz_data["questions"]:
                user_answers[q["id"]] = q["answer"]

            response = await client.post(
                "/api/quiz/analyze",
                json={
                    "subject": "测试",
                    "topic": "测试",
                    "questions": quiz_data["questions"],
                    "userAnswers": user_answers,
                    "duration": 60,
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "summary" in data["data"]


# ============================================================
# XP 和等级计算单元测试
# ============================================================

class TestXpCalculation:
    """测试 XP 计算逻辑"""

    def test_calculate_level(self):
        """测试等级计算"""
        from app.services.user_service import calculate_level

        assert calculate_level(0) == 1
        assert calculate_level(50) == 1
        assert calculate_level(100) == 2
        assert calculate_level(200) == 2
        assert calculate_level(300) == 3
        assert calculate_level(600) == 4
        assert calculate_level(1000) == 5
        assert calculate_level(2000) == 6
        assert calculate_level(3000) == 6

    def test_get_level_title(self):
        """测试等级称号"""
        from app.services.user_service import get_level_title

        assert get_level_title(1) == "初学者"
        assert get_level_title(2) == "学徒"
        assert get_level_title(3) == "探究者"
        assert get_level_title(4) == "学者"
        assert get_level_title(5) == "大师"
        assert get_level_title(6) == "传奇"
        assert get_level_title(7) == "传奇"

    def test_calculate_xp_earned(self):
        """测试 XP 计算"""
        from app.services.user_service import calculate_xp_earned

        # 5题全对，首次闯关
        xp = calculate_xp_earned(5, 5, is_first_quiz=True)
        assert xp == 5 * 10 + (5 - 1) * 5 + 50 + 20  # 50 + 20 + 50 + 20 = 140
        assert xp == 140

        # 3题全对，非首次
        xp = calculate_xp_earned(3, 3, is_first_quiz=False)
        assert xp == 3 * 10 + (3 - 1) * 5 + 20  # 30 + 10 + 20 = 60
        assert xp == 60

        # 5对3，非首次
        xp = calculate_xp_earned(3, 5, is_first_quiz=False)
        assert xp == 3 * 10 + (3 - 1) * 5  # 30 + 10 = 40
        assert xp == 40


# ============================================================
# 扩展测试：验证现有核心功能不受影响
# ============================================================

class TestExistingCoreFunctions:
    """验证现有核心功能不受影响"""

    @pytest.mark.asyncio
    async def test_health_check_still_works(self, app):
        """健康检查应仍然正常工作"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"

    @pytest.mark.asyncio
    async def test_quiz_generate_still_works(self, app):
        """出题接口应仍然正常工作"""
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
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]["questions"]) == 3

    @pytest.mark.asyncio
    async def test_quiz_analyze_still_works(self, app):
        """分析报告接口应仍然正常工作"""
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 先出题
            gen_resp = await client.post(
                "/api/quiz/generate",
                json={
                    "subject": "测试",
                    "topic": "测试",
                    "count": 2,
                    "difficulty": "medium",
                    "type": "single",
                },
            )
            quiz_data = gen_resp.json()["data"]

            # 分析
            user_answers = {}
            for q in quiz_data["questions"]:
                user_answers[q["id"]] = q["answer"]

            response = await client.post(
                "/api/quiz/analyze",
                json={
                    "subject": "测试",
                    "topic": "测试",
                    "questions": quiz_data["questions"],
                    "userAnswers": user_answers,
                    "duration": 60,
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "summary" in data["data"]
