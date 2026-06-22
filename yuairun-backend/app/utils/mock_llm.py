"""Mock LLM 实现，用于开发和测试阶段模拟 DeepSeek API"""

import json
import uuid
from datetime import datetime, timezone


def get_mock_quiz_response(subject: str, topic: str, count: int) -> dict:
    """生成模拟的出题响应"""
    mock_questions = [
        {
            "id": f"q_{uuid.uuid4().hex[:8]}",
            "type": "single",
            "question": f"关于「{topic}」的核心概念，以下哪项描述是正确的？",
            "options": [
                {"label": "A", "content": f"「{topic}」的核心思想起源于20世纪90年代，最初是为解决特定领域的工程问题而提出的理论框架"},
                {"label": "B", "content": f"「{topic}」强调通过迭代式和增量式的实践方法，在复杂环境中持续交付价值和获得反馈"},
                {"label": "C", "content": f"「{topic}」主张采用自上而下的严格规划模式，在项目启动前完成全部需求分析"},
                {"label": "D", "content": f"「{topic}」主要关注文档完整性和流程规范性，而非实际产出的质量和效率"},
            ],
            "answer": "B",
            "explanation": f"「{topic}」的核心是迭代式、价值驱动的实践方法。它强调快速反馈、持续改进和适应性规划，而非一次性完整规划。B选项准确描述了其核心理念。",
            "difficulty": "medium",
            "knowledgePoint": topic,
        },
        {
            "id": f"q_{uuid.uuid4().hex[:8]}",
            "type": "single",
            "question": f"在实际应用「{topic}」时，以下哪种做法是常见的误解？",
            "options": [
                {"label": "A", "content": f"将{topic}视为可以解决所有问题的银弹，盲目套用而不考虑具体上下文"},
                {"label": "B", "content": f"根据团队实际情况对{topic}的实践进行适当裁剪和调整"},
                {"label": "C", "content": f"在实施{topic}过程中定期回顾和反思，持续改进工作方式"},
                {"label": "D", "content": f"注重{topic}中人与协作的价值，建立自组织团队文化"},
            ],
            "answer": "A",
            "explanation": f"「{topic}」并非万能银弹。常见误解包括认为它可以解决所有问题、不需要前期规划等。实际上，{topic}需要根据具体场景灵活应用。",
            "difficulty": "easy",
            "knowledgePoint": topic,
        },
        {
            "id": f"q_{uuid.uuid4().hex[:8]}",
            "type": "single",
            "question": f"「{topic}」在实践中取得成功的关键因素是什么？",
            "options": [
                {"label": "A", "content": "购买最贵的工具和最先进的软件，工具决定一切"},
                {"label": "B", "content": "严格执行预设的流程和规范，不允许任何偏差"},
                {"label": "C", "content": "建立信任文化、促进跨职能协作、鼓励持续学习和快速反馈"},
                {"label": "D", "content": "增加管理层级和审批流程，确保每个决策都经过多级审核"},
            ],
            "answer": "C",
            "explanation": f"「{topic}」成功的关键在于人和文化，而非工具或流程。信任、协作、持续改进的文化氛围比严格的流程更重要。",
            "difficulty": "medium",
            "knowledgePoint": topic,
        },
        {
            "id": f"q_{uuid.uuid4().hex[:8]}",
            "type": "judge",
            "question": f"判断题：采用「{topic}」意味着不需要任何文档和前期规划。",
            "options": [
                {"label": "A", "content": "正确"},
                {"label": "B", "content": "错误"},
            ],
            "answer": "B",
            "explanation": f"「{topic}」并非完全不需要文档和规划，而是强调「恰到好处」的文档和适应性规划，避免过度文档化和僵化的计划。",
            "difficulty": "easy",
            "knowledgePoint": topic,
        },
        {
            "id": f"q_{uuid.uuid4().hex[:8]}",
            "type": "single",
            "question": f"在「{topic}」的实践中，如何有效衡量团队的进步和效果？",
            "options": [
                {"label": "A", "content": "以代码行数和文档页数作为核心度量指标，数量越多说明效果越好"},
                {"label": "B", "content": "通过可交付产品的价值、客户满意度、团队士气以及交付周期等多维度综合评估"},
                {"label": "C", "content": "只看项目的预算执行率，花费越少说明管理越成功"},
                {"label": "D", "content": "以团队加班时长作为衡量标准，加班越多代表团队越努力"},
            ],
            "answer": "B",
            "explanation": f"「{topic}」强调以价值为导向的评估方式。代码行数、加班时长等是误导性指标。真正的进步体现在交付的价值、质量和团队健康度上。",
            "difficulty": "hard",
            "knowledgePoint": topic,
            "knowledgeSource": "model_knowledge",
        },
    ]

    # 截取请求的数量
    questions = mock_questions[:count]

    return {
        "questions": questions,
        "metadata": {
            "subject": subject,
            "topic": topic,
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "model": "mock-deepseek-chat",
            "searchEnhanced": False,
            "searchSources": [],
        },
    }


def get_mock_report_response(
    subject: str,
    topic: str,
    questions: list,
    user_answers: dict,
    duration: int,
) -> dict:
    """生成模拟的分析报告响应"""
    total = len(questions)
    correct = 0
    wrong_questions = []
    for q in questions:
        qid = q.get("id", "")
        user_ans = user_answers.get(qid, "")
        correct_ans = q.get("answer", "")
        if isinstance(correct_ans, list):
            if isinstance(user_ans, list) and sorted(user_ans) == sorted(correct_ans):
                correct += 1
            else:
                wrong_questions.append(q)
        else:
            if str(user_ans) == str(correct_ans):
                correct += 1
            else:
                wrong_questions.append(q)

    accuracy = correct / total if total > 0 else 0
    score = int(accuracy * 100)

    weak_points = [f"{topic}的细节理解", f"{topic}的实际应用"] if accuracy < 0.8 else []
    strong_points = [f"{topic}的基础概念"] if accuracy >= 0.5 else []

    return {
        "summary": f"你在「{topic}」方面的掌握程度为{'优秀' if accuracy >= 0.8 else '中等偏上' if accuracy >= 0.6 else '一般'}。"
                    f"答对 {correct}/{total} 题（{score}%）。"
                    f"{'基础知识掌握扎实，但对细节理解还需加强。' if weak_points else '整体表现不错，继续保持！'}"
                    f"建议多做练习，巩固薄弱环节。",
        "score": score,
        "accuracy": accuracy,
        "weakPoints": weak_points if weak_points else ["无明显薄弱点"],
        "strongPoints": strong_points if strong_points else [f"{topic}的基本认知"],
        "suggestions": [
            f"建议系统复习「{topic}」的核心概念",
            "可以通过画思维导图的方式整理知识框架",
            "尝试将理论与实际应用场景结合理解",
        ],
        "recommendedTopics": [
            f"{topic}的进阶知识",
            f"{topic}的实际案例分析",
        ],
        "detailedAnalysis": f"━━━ 详细分析 ━━━\n\n"
                           f"▎总体表现\n"
                           f"你在「{topic}」的测试中取得了 {score}分（{correct}/{total}），"
                           f"用时 {duration} 秒。\n\n"
                           f"▎知识掌握情况\n"
                           f"· 基础概念：{'✅ 掌握良好' if accuracy >= 0.6 else '⚠️ 需要加强'}\n"
                           f"· 理解应用：{'✅ 掌握良好' if accuracy >= 0.8 else '⚠️ 需要加强'}\n\n"
                           f"▎学习建议\n"
                           f"1. 建议重点复习薄弱知识点\n"
                           f"2. 多做练习题巩固理解\n"
                           f"3. 结合实际案例加深印象\n\n"
                           f"▎推荐资源\n"
                           f"· 相关教材和在线课程\n"
                           f"· 实践项目练习\n"
                           f"学习是一个持续的过程，保持耐心和热情！",
    }
