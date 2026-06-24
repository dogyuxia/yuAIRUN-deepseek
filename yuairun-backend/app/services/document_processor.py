"""文档处理服务 — 解析 → 分块 → 向量化 → 入库"""

import logging
import os
from typing import Optional

from app.services.vector_service import add_document_chunks
from app.services.embedding_service import get_embeddings

logger = logging.getLogger(__name__)


async def process_document(
    file_path: str,
    kb_id: str,
    doc_id: str,
    filename: str,
) -> int:
    """
    处理单份文档：Docling 解析 → HybridChunker 分块 → 向量化 → 存入 ChromaDB
    
    Args:
        file_path: 文件绝对路径
        kb_id: 知识库 ID
        doc_id: 文档 ID
        filename: 文件名
        
    Returns:
        分块数量（0 表示处理失败）
    """
    try:
        # 1. Docling 解析文档
        chunks = await _parse_with_docling(file_path)
        
        if not chunks:
            logger.warning("文档解析后为空: %s", filename)
            return 0
        
        # 2. 存入 ChromaDB
        chunk_count = await add_document_chunks(
            kb_id=kb_id,
            doc_id=doc_id,
            filename=filename,
            chunks=chunks,
        )
        
        logger.info("✅ 文档处理完成: %s → %d 个分块", filename, chunk_count)
        return chunk_count
    
    except Exception as e:
        logger.error("文档处理失败 %s: %s", filename, e)
        return 0


async def _parse_with_docling(file_path: str) -> list[str]:
    """
    使用 Docling 解析文档并返回文本分块列表
    
    支持格式: PDF, DOCX, PPTX, HTML, Images, TXT, MD
    
    Args:
        file_path: 文件路径
        
    Returns:
        文本分块列表
    """
    try:
        from langchain_docling import DoclingLoader
        from docling.chunking import HybridChunker
        
        # 使用 HybridChunker 按语义分块
        embeddings = get_embeddings()
        if embeddings:
            try:
                from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
                tokenizer = HuggingFaceTokenizer.from_pretrained(
                    "BAAI/bge-m3",
                    cache_dir=os.environ.get("EMBEDDING_CACHE_DIR"),
                )
                chunker = HybridChunker(tokenizer=tokenizer, max_tokens=512)
            except Exception:
                chunker = None
        else:
            chunker = None
        
        loader = DoclingLoader(
            file_path=[file_path],
            chunker=chunker,
        )
        docs = loader.load()
        
        # 提取文本内容
        texts = [doc.page_content for doc in docs if doc.page_content.strip()]
        
        if not texts:
            # Docling 解析失败，降级使用基础文本提取
            texts = await _fallback_extract_text(file_path)
        
        return texts
    
    except ImportError:
        logger.warning("Docling 未安装，使用基础文本提取降级方案")
        return await _fallback_extract_text(file_path)
    except Exception as e:
        logger.warning("Docling 解析失败，使用基础文本提取降级: %s", e)
        return await _fallback_extract_text(file_path)


async def _fallback_extract_text(file_path: str) -> list[str]:
    """
    基础文本提取降级方案——不使用 Docling 时使用
    
    Args:
        file_path: 文件路径
        
    Returns:
        文本分块列表
    """
    ext = os.path.splitext(file_path)[1].lower()
    full_text = ""
    
    try:
        if ext == ".txt":
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                full_text = f.read()
        elif ext == ".md":
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                full_text = f.read()
        elif ext == ".pdf":
            # 尝试 PyMuPDF
            try:
                import fitz
                doc = fitz.open(file_path)
                full_text = "\n".join([page.get_text() for page in doc])
                doc.close()
            except ImportError:
                pass
        elif ext == ".docx":
            try:
                from docx import Document
                doc = Document(file_path)
                full_text = "\n".join([p.text for p in doc.paragraphs])
            except ImportError:
                pass
    except Exception as e:
        logger.error("基础文本提取失败: %s", e)
        return []
    
    if not full_text.strip():
        return []
    
    # 使用 RecursiveCharacterTextSplitter 分块
    try:
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100,
            separators=["\n\n", "\n", "。", ".", " ", ""],
        )
        chunks = splitter.split_text(full_text)
        return [c for c in chunks if c.strip()]
    except ImportError:
        # 极端降级：按段落分块
        paragraphs = [p.strip() for p in full_text.split("\n\n") if p.strip()]
        chunks = []
        current = ""
        for p in paragraphs:
            if len(current) + len(p) < 500:
                current += "\n" + p
            else:
                if current:
                    chunks.append(current)
                current = p
        if current:
            chunks.append(current)
        return chunks
