"""知识库检索工具 — 封装 ChromaDB 查询为 LangChain Tool"""

import logging

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from app.services.vector_service import search_similar_chunks

logger = logging.getLogger(__name__)


class KnowledgeBaseRetrieverInput(BaseModel):
    """KnowledgeBaseRetriever 的输入参数"""
    query: str = Field(description="搜索查询文本，通常是用户输入的知识点或学习内容")
    k: int = Field(default=5, description="返回的结果数量（3-10）")


class KnowledgeBaseRetriever(BaseTool):
    """
    从 ChromaDB 知识库中检索与查询最相似的知识块。

    该工具封装了 vector_service.search_similar_chunks()，
    将检索结果格式化为结构化的文本，供 AI Agent 作为出题参考材料。

    当用户选择了知识库时，AI Agent 应优先调用此工具获取知识库内容。
    """

    name: str = "knowledge_base_retriever"
    description: str = (
        "从指定的私有知识库中检索与查询相关的知识内容。"
        "当用户已选择知识库时，优先使用此工具获取参考资料。"
        "输入参数：query（搜索关键词），k（返回结果数量，默认5条）"
    )
    args_schema: type = KnowledgeBaseRetrieverInput

    kb_id: str = Field(description="知识库 ID，创建时指定")
    kb_name: str = Field(default="", description="知识库名称，用于标注来源")

    def _run(self, query: str, k: int = 5) -> str:
        """同步检索（兜底使用）"""
        import asyncio
        return asyncio.run(self._arun(query, k))

    async def _arun(self, query: str, k: int = 5) -> str:
        """异步检索，返回格式化后的文本"""
        try:
            chunks = await search_similar_chunks(
                query=query,
                kb_id=self.kb_id,
                k=min(k, 10),  # 最多返回10条
            )

            if not chunks:
                return "【知识库检索结果为空】在知识库中没有找到与查询相关的内容。"

            lines = []
            for i, chunk in enumerate(chunks, 1):
                source = chunk["metadata"].get("filename", "未知来源")
                lines.append(f"--- 知识库资料 {i} ---")
                lines.append(f"来源：{source}")
                lines.append(f"内容：{chunk['text']}")
                lines.append("")

            kb_label = f"知识库：{self.kb_name}" if self.kb_name else f"知识库ID：{self.kb_id}"
            header = f"【知识库检索结果】{kb_label}，共找到 {len(chunks)} 条相关内容：\n\n"
            return header + "\n".join(lines)

        except Exception as e:
            logger.error("KnowledgeBaseRetriever 检索失败: %s", e)
            return "【知识库检索异常】检索过程中发生错误，请稍后重试或使用联网搜索。"
