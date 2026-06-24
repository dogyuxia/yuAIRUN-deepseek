"""测试 API 端点"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import create_app
from app.models.quiz import GenerateQuizRequest, QuizResponse
from app.models.report import AnalyzeQuizRequest, AnalyzeReportData


@pytest.fixture(autouse=True)
def _mock_settings():
    """确保每次测试使用干净的 Mock LLM 配置"""
    from app.config import get_settings
    get_settings.cache_clear()
    # 设置环境变量，强制 Mock 模式
    import os
    os.environ.setdefault("USE_MOCK_LLM", "true")
    yield
    get_settings.cache_clear()


@pytest.fixture
def app():
    """创建测试用应用实例"""
    return create_app()


@pytest.mark.asyncio
async def test_health_check(app):
    """测试健康检查端点"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "yuAIRUN Backend"


@pytest.mark.asyncio
async def test_generate_quiz_success(app):
    """测试出题接口成功响应"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/quiz/generate",
            json={
                "subject": "计算机网络",
                "topic": "TCP三次握手的过程和原理",
                "count": 5,
                "difficulty": "medium",
                "type": "single",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert len(data["data"]["questions"]) == 5

        # 验证题目结构
        first_q = data["data"]["questions"][0]
        assert "id" in first_q
        assert "question" in first_q
        assert "options" in first_q
        assert "answer" in first_q
        assert "explanation" in first_q
        assert "difficulty" in first_q

        # 验证元数据
        assert data["data"]["metadata"]["subject"] == "计算机网络"


@pytest.mark.asyncio
async def test_generate_quiz_validation(app):
    """测试出题接口参数校验"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 缺少必填字段
        response = await client.post(
            "/api/quiz/generate",
            json={"subject": "测试"},
        )
        assert response.status_code == 422

        # count 超出范围
        response = await client.post(
            "/api/quiz/generate",
            json={
                "subject": "测试",
                "topic": "测试",
                "count": 100,
                "difficulty": "medium",
                "type": "single",
            },
        )
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_analyze_quiz_success(app):
    """测试分析报告接口成功响应"""
    # 先生成题目
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        gen_response = await client.post(
            "/api/quiz/generate",
            json={
                "subject": "计算机网络",
                "topic": "TCP三次握手",
                "count": 3,
                "difficulty": "medium",
                "type": "single",
            },
        )
        quiz_data = gen_response.json()["data"]

        # 构造用户答案（全部答对）
        user_answers = {}
        for q in quiz_data["questions"]:
            user_answers[q["id"]] = q["answer"]

        # 请求分析报告
        response = await client.post(
            "/api/quiz/analyze",
            json={
                "subject": "计算机网络",
                "topic": "TCP三次握手",
                "questions": quiz_data["questions"],
                "userAnswers": user_answers,
                "duration": 120,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        report = data["data"]
        assert "summary" in report
        assert "score" in report
        assert "accuracy" in report
        assert "suggestions" in report
        assert "detailedAnalysis" in report


@pytest.mark.asyncio
async def test_analyze_quiz_validation(app):
    """测试分析报告接口参数校验"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 缺少必填字段
        response = await client.post(
            "/api/quiz/analyze",
            json={"subject": "测试"},
        )
        assert response.status_code == 422


@pytest.mark.asyncio
async def test_full_workflow(app):
    """测试完整工作流：出题 → 答题 → 分析报告"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Step 1: 生成题目
        gen_resp = await client.post(
            "/api/quiz/generate",
            json={
                "subject": "Python",
                "topic": "装饰器",
                "count": 5,
                "difficulty": "mixed",
                "type": "mixed",
            },
        )
        assert gen_resp.status_code == 200
        gen_data = gen_resp.json()
        assert gen_data["success"] is True
        questions = gen_data["data"]["questions"]
        assert len(questions) == 5

        # Step 2: 模拟答题（部分答对）
        user_answers = {}
        for i, q in enumerate(questions):
            if i % 2 == 0:
                user_answers[q["id"]] = q["answer"]  # 答对
            else:
                # 答错
                wrong = "A" if q["answer"] != "A" else "B"
                user_answers[q["id"]] = wrong

        # Step 3: 生成分析报告
        report_resp = await client.post(
            "/api/quiz/analyze",
            json={
                "subject": "Python",
                "topic": "装饰器",
                "questions": questions,
                "userAnswers": user_answers,
                "duration": 180,
            },
        )
        assert report_resp.status_code == 200
        report_data = report_resp.json()
        assert report_data["success"] is True
        assert 0 <= report_data["data"]["score"] <= 100
        assert report_data["data"]["accuracy"] == 0.6  # 3/5
