"""测试 LangChain 链（使用 Mock）"""

import pytest
from app.chains.quiz_chain import MockQuizChain
from app.chains.report_chain import MockReportChain
from app.models.quiz import QuizResponse
from app.models.report import AnalyzeReportData


class TestMockQuizChain:
    """测试 Mock 出题链"""

    @pytest.mark.asyncio
    async def test_ainvoke_returns_quiz_response(self):
        """测试异步调用返回 QuizResponse 类型"""
        chain = MockQuizChain()
        result = await chain.ainvoke({
            "subject": "计算机网络",
            "topic": "TCP三次握手",
            "count": 5,
            "difficulty": "medium",
            "type": "single",
        })
        assert isinstance(result, QuizResponse)
        assert len(result.questions) == 5

    def test_invoke_returns_quiz_response(self):
        """测试同步调用返回 QuizResponse 类型"""
        chain = MockQuizChain()
        result = chain.invoke({
            "subject": "计算机网络",
            "topic": "TCP三次握手",
            "count": 3,
            "difficulty": "easy",
            "type": "single",
        })
        assert isinstance(result, QuizResponse)
        assert len(result.questions) == 3

    @pytest.mark.asyncio
    async def test_questions_have_required_fields(self):
        """测试题目包含所有必要字段"""
        chain = MockQuizChain()
        result = await chain.ainvoke({
            "subject": "Python",
            "topic": "装饰器",
            "count": 5,
            "difficulty": "medium",
            "type": "single",
        })

        for q in result.questions:
            assert q.id, "题目必须有ID"
            assert q.question, "题目必须有内容"
            assert q.type in ("single", "multiple", "judge"), "题目类型必须有效"
            assert len(q.options) >= 2, "题目至少有两个选项"
            assert q.answer, "题目必须有答案"
            assert q.explanation, "题目必须有解析"
            assert q.difficulty in ("easy", "medium", "hard"), "难度必须有效"

    @pytest.mark.asyncio
    async def test_metadata_is_present(self):
        """测试元数据完整"""
        chain = MockQuizChain()
        result = await chain.ainvoke({
            "subject": "测试学科",
            "topic": "测试主题",
            "count": 5,
            "difficulty": "medium",
            "type": "single",
        })
        assert result.metadata.subject == "测试学科"
        assert result.metadata.topic == "测试主题"
        assert result.metadata.model == "mock-deepseek-chat"

    @pytest.mark.asyncio
    async def test_different_counts(self):
        """测试不同题目数量"""
        chain = MockQuizChain()
        for count in [1, 3, 5]:
            result = await chain.ainvoke({
                "subject": "Math",
                "topic": "代数",
                "count": count,
                "difficulty": "medium",
                "type": "single",
            })
            assert len(result.questions) == count


class TestMockReportChain:
    """测试 Mock 分析报告链"""

    @staticmethod
    def _make_sample_data():
        """生成样例答题数据"""
        chain = MockQuizChain()
        quiz = chain.invoke({
            "subject": "计算机网络",
            "topic": "TCP三次握手",
            "count": 5,
            "difficulty": "medium",
            "type": "single",
        })
        questions = [q.model_dump() for q in quiz.questions]
        user_answers = {}
        for q in quiz.questions:
            if isinstance(q.answer, list):
                user_answers[q.id] = q.answer
            else:
                user_answers[q.id] = q.answer
        # 模拟第一题答错
        if questions:
            first_q = questions[0]
            if isinstance(first_q["answer"], list):
                user_answers[first_q["id"]] = ["wrong"]
            else:
                correct = first_q["answer"]
                wrong = "A" if correct != "A" else "B"
                user_answers[first_q["id"]] = wrong

        return {
            "subject": "计算机网络",
            "topic": "TCP三次握手",
            "questions": questions,
            "userAnswers": user_answers,
            "duration": 120,
        }

    @pytest.mark.asyncio
    async def test_ainvoke_returns_report(self):
        """测试异步调用返回 AnalyzeReportData 类型"""
        chain = MockReportChain()
        result = await chain.ainvoke({
            "subject": "测试",
            "topic": "测试主题",
            "questions": [],
            "userAnswers": {},
            "duration": 0,
        })
        assert isinstance(result, AnalyzeReportData)

    @pytest.mark.asyncio
    async def test_report_has_required_fields(self):
        """测试报告包含所有必要字段"""
        chain = MockReportChain()
        data = self._make_sample_data()
        result = await chain.ainvoke(data)

        assert result.summary, "必须有整体评估"
        assert 0 <= result.score <= 100, "得分必须在0-100之间"
        assert 0 <= result.accuracy <= 1, "正确率必须在0-1之间"
        assert len(result.suggestions) > 0, "必须有学习建议"
        assert result.detailedAnalysis, "必须有详细分析"

    @pytest.mark.asyncio
    async def test_report_content_consistency(self):
        """测试报告内容一致性"""
        chain = MockReportChain()

        # 全部答对
        quiz_chain = MockQuizChain()
        quiz = quiz_chain.invoke({
            "subject": "测试", "topic": "测试", "count": 3,
            "difficulty": "medium", "type": "single",
        })
        correct_answers = {q.id: q.answer for q in quiz.questions}
        questions_dict = [q.model_dump() for q in quiz.questions]

        result = await chain.ainvoke({
            "subject": "测试",
            "topic": "测试",
            "questions": questions_dict,
            "userAnswers": correct_answers,
            "duration": 60,
        })

        # 全部答对应该得分较高
        assert result.score >= 80
        assert result.accuracy >= 0.8
