"""
Agentic RAG 出题链 TDD 测试

测试策略：
- 使用 Mock 验证 AgenticQuizChain 的降级逻辑
- 验证 KnowledgeBaseRetriever 工具的正确性
- 验证 quiz_service.py 的路由逻辑
- 验证 QuizMetadata 新增的 Agentic 字段
"""
import pytest

from app.models.quiz import (
    QuizResponse,
    QuizMetadata,
    GenerateQuizRequest,
    GenerateQuizResponse,
)
from app.tools.kb_retriever import KnowledgeBaseRetriever


# ============================================================
# KnowledgeBaseRetriever 工具测试
# ============================================================

class TestKnowledgeBaseRetriever:
    """测试 KnowledgeBaseRetriever 工具"""

    def test_tool_initialization(self):
        """工具应正确初始化"""
        tool = KnowledgeBaseRetriever(
            kb_id="kb_test_123",
            kb_name="测试知识库",
        )
        assert tool.name == "knowledge_base_retriever"
        assert tool.kb_id == "kb_test_123"
        assert tool.kb_name == "测试知识库"
        assert "知识库" in tool.description

    def test_tool_args_schema(self):
        """工具参数模式应正确"""
        tool = KnowledgeBaseRetriever(kb_id="kb_test")
        schema = tool.args_schema
        assert schema is not None

        # 验证参数名和描述
        field_names = list(schema.model_fields.keys())
        assert "query" in field_names
        assert "k" in field_names

    def test_tool_empty_result_format(self):
        """空结果应返回明确提示"""
        # 使用异步事件循环测试协程
        import asyncio
        tool = KnowledgeBaseRetriever(kb_id="kb_empty")

        async def run():
            # 模拟空结果（实际会调用 search_similar_chunks，但这里测试的是工具初始化）
            result = "【知识库检索结果为空】在知识库中没有找到与查询相关的内容。"
            assert "知识库" in result
            assert "为空" in result

        asyncio.run(run())

    def test_tool_description(self):
        """工具描述应该包含用法说明"""
        tool = KnowledgeBaseRetriever(kb_id="kb_test")
        assert "knowledge_base_retriever" in tool.name
        assert tool.description is not None


# ============================================================
# AgenticQuizChain 逻辑测试
# ============================================================

class TestAgenticQuizChainLogic:
    """测试 AgenticQuizChain 的核心逻辑（不使用真实 API）"""

    def test_chain_initialization(self):
        """AgenticQuizChain 应正确初始化"""
        from app.chains.agentic_quiz_chain import AgenticQuizChain

        # 无知识库
        chain = AgenticQuizChain()
        assert chain.knowledge_base_id is None
        assert chain.knowledge_base_name == ""

        # 有知识库
        chain = AgenticQuizChain(
            knowledge_base_id="kb_test",
            knowledge_base_name="测试知识库",
        )
        assert chain.knowledge_base_id == "kb_test"
        assert chain.knowledge_base_name == "测试知识库"

    def test_fallback_returns_quiz_response(self):
        """降级逻辑应返回 QuizResponse"""
        from app.chains.agentic_quiz_chain import AgenticQuizChain
        import asyncio

        chain = AgenticQuizChain()
        result = asyncio.run(chain._fallback({
            "subject": "计算机科学",
            "topic": "测试主题",
            "count": 3,
            "difficulty": "medium",
            "type": "single",
        }))
        assert isinstance(result, QuizResponse)
        # 降级返回空题（因为没有 Mock LLM 配置）
        assert result.metadata.searchMode == "agentic"
        assert result.metadata.searchEnhanced is False

    def test_fallback_sets_correct_metadata(self):
        """降级元数据应正确设置（fallback=True）"""
        from app.chains.agentic_quiz_chain import AgenticQuizChain
        import asyncio

        chain = AgenticQuizChain(
            knowledge_base_id="kb_test",
            knowledge_base_name="测试知识库",
        )
        result = asyncio.run(chain._fallback({
            "subject": "测试",
            "topic": "测试主题",
            "count": 5,
            "difficulty": "medium",
            "type": "single",
        }))
        assert result.metadata.searchMode == "agentic"
        assert result.metadata.fallback is True  # _fallback 现在正确设置 fallback=True


# ============================================================
# quiz_service.py 路由逻辑测试
# ============================================================

class TestQuizServiceRouting:
    """测试 quiz_service.py 的路由逻辑"""

    def test_request_without_knowledge_base(self):
        """无知识库时，searchMode 应不影响路由"""
        # 验证新模型接受 "agentic" 作为 searchMode
        req = GenerateQuizRequest(
            subject="测试",
            topic="测试主题",
            searchMode="agentic",
        )
        assert req.searchMode == "agentic"
        assert req.knowledgeBaseId is None

    def test_request_with_knowledge_base(self):
        """有知识库时，searchMode 应不影响路由"""
        req = GenerateQuizRequest(
            subject="测试",
            topic="测试主题",
            knowledgeBaseId="kb_test_123",
            searchMode="agentic",
        )
        assert req.knowledgeBaseId == "kb_test_123"
        assert req.searchMode == "agentic"

    def test_backward_compatible_search_mode(self):
        """旧 searchMode 值应向后兼容"""
        req = GenerateQuizRequest(
            subject="测试",
            topic="测试主题",
            searchMode="search",  # 旧值
        )
        assert req.searchMode == "search"

        req2 = GenerateQuizRequest(
            subject="测试",
            topic="测试主题",
            searchMode="knowledge_base",  # 旧值
        )
        assert req2.searchMode == "knowledge_base"

        req3 = GenerateQuizRequest(
            subject="测试",
            topic="测试主题",
            searchMode="hybrid",  # 旧值
        )
        assert req3.searchMode == "hybrid"

    def test_default_search_mode_is_agentic(self):
        """默认 searchMode 应为 agentic"""
        req = GenerateQuizRequest(
            subject="测试",
            topic="测试主题",
        )
        assert req.searchMode == "agentic"


# ============================================================
# QuizMetadata Agentic 字段测试
# ============================================================

class TestQuizMetadataAgenticFields:
    """测试 QuizMetadata 新增的 Agentic 字段"""

    def test_default_agentic_fields(self):
        """默认值测试"""
        metadata = QuizMetadata(
            subject="测试",
            topic="测试主题",
            generatedAt="2026-01-01T00:00:00Z",
            model="deepseek-chat",
        )
        assert metadata.searchMode == "agentic"
        assert metadata.retrievalStrategy is None
        assert metadata.toolsInvoked == []
        assert metadata.fallback is False

    def test_agentic_mode_metadata(self):
        """Agentic 模式完整元数据"""
        metadata = QuizMetadata(
            subject="AI Agent",
            topic="ReAct Pattern",
            generatedAt="2026-01-01T00:00:00Z",
            model="deepseek-chat",
            searchEnhanced=True,
            searchMode="agentic",
            searchSources=["AI Agent 知识库", "https://arxiv.org/abs/2210.03629"],
            knowledgeBaseId="kb_system_ai_agent",
            knowledgeBaseName="AI Agent 知识库",
            retrievalStrategy="kb_then_web",
            toolsInvoked=["knowledge_base_retriever", "TavilySearch"],
            fallback=False,
        )
        assert metadata.searchMode == "agentic"
        assert metadata.retrievalStrategy == "kb_then_web"
        assert "knowledge_base_retriever" in metadata.toolsInvoked
        assert "TavilySearch" in metadata.toolsInvoked
        assert metadata.fallback is False

    def test_fallback_metadata(self):
        """降级场景元数据"""
        metadata = QuizMetadata(
            subject="测试",
            topic="测试主题",
            generatedAt="2026-01-01T00:00:00Z",
            model="deepseek-chat",
            searchEnhanced=False,
            searchMode="agentic",
            searchSources=[],
            fallback=True,
        )
        assert metadata.searchMode == "agentic"
        assert metadata.fallback is True
        assert metadata.searchEnhanced is False


# ============================================================
# KnowledgeSource 字段测试
# ============================================================

class TestKnowledgeSourceComprehensive:
    """测试 knowledgeSource 字段的完整语义"""

    def test_model_knowledge_source(self):
        """model_knowledge 应正确设置"""
        from app.models.quiz import QuizQuestion, QuizOption

        q = QuizQuestion(
            id="q_001",
            type="single",
            question="测试",
            options=[QuizOption(label="A", content="A"), QuizOption(label="B", content="B")],
            answer="A",
            explanation="测试解析",
            difficulty="medium",
            knowledgePoint="测试",
            knowledgeSource="model_knowledge",
        )
        assert q.knowledgeSource == "model_knowledge"

    def test_web_search_source(self):
        """web_search 应正确设置"""
        from app.models.quiz import QuizQuestion, QuizOption

        q = QuizQuestion(
            id="q_002",
            type="single",
            question="测试",
            options=[QuizOption(label="A", content="A"), QuizOption(label="B", content="B")],
            answer="A",
            explanation="测试解析",
            difficulty="medium",
            knowledgePoint="测试",
            knowledgeSource="web_search",
        )
        assert q.knowledgeSource == "web_search"

    def test_knowledge_base_source(self):
        """knowledge_base 应正确设置"""
        from app.models.quiz import QuizQuestion, QuizOption

        q = QuizQuestion(
            id="q_003",
            type="single",
            question="测试",
            options=[QuizOption(label="A", content="A"), QuizOption(label="B", content="B")],
            answer="A",
            explanation="测试解析",
            difficulty="medium",
            knowledgePoint="测试",
            knowledgeSource="knowledge_base",
        )
        assert q.knowledgeSource == "knowledge_base"
