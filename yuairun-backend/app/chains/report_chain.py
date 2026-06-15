"""分析报告 LangChain 链定义"""

import json
import re

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from app.config import get_settings
from app.models.report import AnalyzeReportData
from app.prompts.report_prompt import REPORT_SYSTEM_PROMPT, REPORT_HUMAN_PROMPT
from app.utils.mock_llm import get_mock_report_response
from app.chains.quiz_chain import parse_json_response


def format_quiz_details(questions: list, user_answers: dict) -> str:
    """格式化题目详情文本"""
    lines = []
    for i, q in enumerate(questions, 1):
        qid = q.get("id", "")
        user_ans = user_answers.get(qid, "未作答")
        correct_ans = q.get("answer", "")
        is_correct = str(user_ans) == str(correct_ans)
        status = "✅" if is_correct else "❌"
        lines.append(
            f"{i}. [{status}] {q.get('question', '')}\n"
            f"   你的答案: {user_ans} | 正确答案: {correct_ans}\n"
        )
    return "\n".join(lines)


def create_report_chain(use_mock: bool = False):
    """
    创建分析报告 LangChain 链

    Args:
        use_mock: 是否使用 Mock LLM（测试用）

    Returns:
        可调用的链对象
    """
    settings = get_settings()

    if use_mock:
        return MockReportChain()

    llm = ChatOpenAI(
        model="deepseek-chat",
        openai_api_key=settings.deepseek_api_key,
        openai_api_base=settings.deepseek_base_url,
        temperature=0.3,  # 分析报告使用较低温度，保证准确性
        timeout=90,
        max_retries=2,
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", REPORT_SYSTEM_PROMPT),
        ("human", REPORT_HUMAN_PROMPT),
    ])

    return ReportChain(llm, prompt)


class ReportChain:
    """分析报告链 - 通过 Prompt 引导 LLM 输出 JSON，手动解析"""

    def __init__(self, llm, prompt):
        self.llm = llm
        self.prompt = prompt

    async def ainvoke(self, inputs: dict) -> AnalyzeReportData:
        chain = self.prompt | self.llm
        result = await chain.ainvoke(inputs)
        parsed = parse_json_response(result.content)
        return AnalyzeReportData(**parsed)

    def invoke(self, inputs: dict) -> AnalyzeReportData:
        chain = self.prompt | self.llm
        result = chain.invoke(inputs)
        parsed = parse_json_response(result.content)
        return AnalyzeReportData(**parsed)


class MockReportChain:
    """Mock 分析报告链，用于开发测试"""

    async def ainvoke(self, inputs: dict) -> AnalyzeReportData:
        """模拟异步调用"""
        import asyncio
        await asyncio.sleep(1.5)  # 模拟网络延迟

        result = get_mock_report_response(
            subject=inputs.get("subject", ""),
            topic=inputs.get("topic", ""),
            questions=inputs.get("questions", []),
            user_answers=inputs.get("userAnswers", {}),
            duration=inputs.get("duration", 0),
        )
        return AnalyzeReportData(**result)

    def invoke(self, inputs: dict) -> AnalyzeReportData:
        """模拟同步调用"""
        result = get_mock_report_response(
            subject=inputs.get("subject", ""),
            topic=inputs.get("topic", ""),
            questions=inputs.get("questions", []),
            user_answers=inputs.get("userAnswers", {}),
            duration=inputs.get("duration", 0),
        )
        return AnalyzeReportData(**result)
