"""
RAG 出题链 TDD 测试

测试策略：
- 验证 knowledgeSource 字段在三种模式下正确设置
- 验证 searchMode 路由逻辑
- 验证 QuizMetadata 新增字段
- 使用 Mock 链模拟 RAG 场景
"""

import pytest
from datetime import datetime, timezone

from app.models.quiz import (
    QuizResponse,
    QuizQuestion,
    QuizMetadata,
    QuizOption,
    GenerateQuizRequest,
)


# ============================================================
# QuizMetadata 新增字段测试
# ============================================================

class TestQuizMetadataFields:
    """测试 QuizMetadata 新增的 RAG 相关字段"""

    def test_metadata_default_search_mode(self):
        """默认 searchMode 应为 search"""
        metadata = QuizMetadata(
            subject="测试",
            topic="测试",
            generatedAt="2026-01-01T00:00:00Z",
            model="deepseek-chat",
        )
        assert metadata.searchMode == "search"
        assert metadata.searchEnhanced is False
        assert metadata.knowledgeBaseId is None
        assert metadata.knowledgeBaseName is None

    def test_metadata_knowledge_base_mode(self):
        """知识库模式 metadata"""
        metadata = QuizMetadata(
            subject="AI Agent",
            topic="ReAct Pattern",
            generatedAt="2026-01-01T00:00:00Z",
            model="deepseek-chat",
            searchEnhanced=True,
            searchMode="knowledge_base",
            searchSources=["AI Agent 知识库 - 01-re-act-pattern.md"],
            knowledgeBaseId="kb_system_ai_agent",
            knowledgeBaseName="AI Agent 知识库",
        )
        assert metadata.searchMode == "knowledge_base"
        assert metadata.knowledgeBaseId == "kb_system_ai_agent"
        assert metadata.knowledgeBaseName == "AI Agent 知识库"
        assert len(metadata.searchSources) == 1

    def test_metadata_hybrid_mode(self):
        """混合模式 metadata"""
        metadata = QuizMetadata(
            subject="AI Agent",
            topic="ReAct Pattern",
            generatedAt="2026-01-01T00:00:00Z",
            model="deepseek-chat",
            searchEnhanced=True,
            searchMode="hybrid",
            searchSources=[
                "AI Agent 知识库 - 01-re-act-pattern.md",
                "https://arxiv.org/abs/2210.03629",
            ],
            knowledgeBaseId="kb_system_ai_agent",
            knowledgeBaseName="AI Agent 知识库",
        )
        assert metadata.searchMode == "hybrid"
        assert len(metadata.searchSources) == 2


# ============================================================
# QuizQuestion knowledgeSource 字段测试
# ============================================================

class TestQuizQuestionKnowledgeSource:
    """测试 QuizQuestion 的 knowledgeSource 字段"""

    def test_default_source_is_model_knowledge(self):
        """默认 knowledgeSource 应为 model_knowledge"""
        q = QuizQuestion(
            id="q_001",
            type="single",
            question="测试题目",
            options=[
                QuizOption(label="A", content="选项A"),
                QuizOption(label="B", content="选项B"),
            ],
            answer="A",
            explanation="解析",
            difficulty="medium",
            knowledgePoint="测试",
        )
        assert q.knowledgeSource == "model_knowledge"

    def test_web_search_source(self):
        """搜索增强来源"""
        q = QuizQuestion(
            id="q_002",
            type="single",
            question="测试题目",
            options=[
                QuizOption(label="A", content="选项A"),
                QuizOption(label="B", content="选项B"),
            ],
            answer="A",
            explanation="解析",
            difficulty="medium",
            knowledgePoint="测试",
            knowledgeSource="web_search",
        )
        assert q.knowledgeSource == "web_search"

    def test_knowledge_base_source(self):
        """知识库来源"""
        q = QuizQuestion(
            id="q_003",
            type="single",
            question="测试题目",
            options=[
                QuizOption(label="A", content="选项A"),
                QuizOption(label="B", content="选项B"),
            ],
            answer="A",
            explanation="解析",
            difficulty="medium",
            knowledgePoint="测试",
            knowledgeSource="knowledge_base",
        )
        assert q.knowledgeSource == "knowledge_base"


# ============================================================
# GenerateQuizRequest 新增字段测试
# ============================================================

class TestGenerateQuizRequestFields:
    """测试 GenerateQuizRequest 新增字段"""

    def test_minimal_request(self):
        """最小请求（无知识库参数）"""
        req = GenerateQuizRequest(
            subject="测试",
            topic="测试主题",
        )
        assert req.knowledgeBaseId is None
        assert req.searchMode == "search"

    def test_knowledge_base_request(self):
        """知识库模式请求"""
        req = GenerateQuizRequest(
            subject="AI Agent",
            topic="ReAct Pattern",
            count=5,
            difficulty="medium",
            type="single",
            knowledgeBaseId="kb_system_ai_agent",
            searchMode="knowledge_base",
        )
        assert req.knowledgeBaseId == "kb_system_ai_agent"
        assert req.searchMode == "knowledge_base"

    def test_hybrid_request(self):
        """混合模式请求"""
        req = GenerateQuizRequest(
            subject="AI Agent",
            topic="ReAct Pattern",
            count=5,
            difficulty="medium",
            type="single",
            knowledgeBaseId="kb_system_ai_agent",
            searchMode="hybrid",
        )
        assert req.searchMode == "hybrid"

    def test_invalid_search_mode(self):
        """无效 searchMode 应校验失败"""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            GenerateQuizRequest(
                subject="测试",
                topic="测试",
                searchMode="invalid",
            )


# ============================================================
# QuizResponse 完整数据结构测试
# ============================================================

class TestQuizResponseStructure:
    """测试 QuizResponse 整体结构"""

    def test_quiz_response_with_knowledge_base_metadata(self):
        """带知识库元数据的完整响应"""
        metadata = QuizMetadata(
            subject="AI Agent",
            topic="ReAct Pattern",
            generatedAt=datetime.now(timezone.utc).isoformat(),
            model="deepseek-chat",
            searchEnhanced=True,
            searchMode="knowledge_base",
            searchSources=["AI Agent 知识库"],
            knowledgeBaseId="kb_system_ai_agent",
            knowledgeBaseName="AI Agent 知识库",
        )

        questions = [
            QuizQuestion(
                id="q_001",
                type="single",
                question="ReAct 模式中，Agent 在调用工具之前应该先做什么？",
                options=[
                    QuizOption(label="A", content="直接调用工具"),
                    QuizOption(label="B", content="思考当前状态和下一步"),
                    QuizOption(label="C", content="等待用户指令"),
                    QuizOption(label="D", content="随机选择一个工具"),
                ],
                answer="B",
                explanation="ReAct 模式中，Agent 先思考（Thought）再行动（Action）。",
                difficulty="medium",
                knowledgePoint="ReAct Pattern",
                knowledgeSource="knowledge_base",
            )
        ]

        response = QuizResponse(questions=questions, metadata=metadata)
        assert len(response.questions) == 1
        assert response.questions[0].knowledgeSource == "knowledge_base"
        assert response.metadata.searchMode == "knowledge_base"
        assert response.metadata.knowledgeBaseName == "AI Agent 知识库"


# ============================================================
# with_structured_output 降级逻辑测试
# ============================================================

class TestStructuredOutputFallback:
    """测试 parse_json_response 降级逻辑"""

    def test_parse_json_direct(self):
        """直接解析纯 JSON"""
        from app.chains.quiz_chain import parse_json_response

        text = '{"questions": [], "metadata": {"subject": "test"}}'
        result = parse_json_response(text)
        assert result["metadata"]["subject"] == "test"
        assert result["questions"] == []

    def test_parse_json_with_code_block(self):
        """解析包含 ```json 代码块的文本"""
        from app.chains.quiz_chain import parse_json_response

        text = '```json\n{"questions": [], "metadata": {"subject": "test"}}\n```'
        result = parse_json_response(text)
        assert result["metadata"]["subject"] == "test"

    def test_parse_json_extra_text(self):
        """解析前后有额外文本的 JSON"""
        from app.chains.quiz_chain import parse_json_response

        text = '这是开头\n{"questions": [{"id": "q_001"}], "metadata": {"subject": "test"}}\n这是结尾'
        result = parse_json_response(text)
        assert len(result["questions"]) == 1
        assert result["questions"][0]["id"] == "q_001"
