"""ChromaDB 向量存储服务"""

import logging
import uuid
from typing import Optional

from app.config import get_settings
from app.services.embedding_service import get_embeddings

logger = logging.getLogger(__name__)

# 单例 ChromaDB 客户端
_client = None
_collection = None


def get_chroma_client():
    """获取 ChromaDB 客户端（单例）"""
    global _client
    if _client is None:
        import chromadb
        settings = get_settings()
        _client = chromadb.PersistentClient(path=settings.chroma_persist_dir)
        logger.info("✅ ChromaDB 客户端初始化成功，持久化路径: %s", settings.chroma_persist_dir)
    return _client


def get_collection():
    """获取或创建 ChromaDB 集合"""
    global _collection
    if _collection is None:
        settings = get_settings()
        client = get_chroma_client()
        
        # 尝试使用 LangChain Chroma 包装（需 HuggingFace Embedding 模型）
        embeddings = get_embeddings()
        if embeddings is not None:
            try:
                from langchain_chroma import Chroma
                vector_store = Chroma(
                    collection_name=settings.chroma_collection_name,
                    embedding_function=embeddings,
                    persist_directory=settings.chroma_persist_dir,
                )
                _collection = vector_store
                logger.info("✅ ChromaDB LangChain 集合就绪 (BGE-M3): %s", settings.chroma_collection_name)
                return _collection
            except Exception as e:
                logger.warning("LangChain Chroma 初始化失败: %s", e)
        
        # 降级：使用原生 ChromaDB（无外部 Embedding 模型）
        # 注意：如果此前集合已用 BGE-M3 (1024维) 创建，原生 ChromaDB
        # 默认用 all-MiniLM-L6-v2 (384维)，会产生维度不匹配错误。
        # 此时删除旧集合重建即可。
        try:
            _collection = client.get_or_create_collection(
                name=settings.chroma_collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            logger.info("✅ ChromaDB 原生集合就绪: %s", settings.chroma_collection_name)
        except Exception as e:
            logger.warning("ChromaDB 集合初始化失败，尝试重建: %s", e)
            try:
                client.delete_collection(settings.chroma_collection_name)
                _collection = client.create_collection(
                    name=settings.chroma_collection_name,
                    metadata={"hnsw:space": "cosine"},
                )
                logger.info("✅ ChromaDB 集合已重建: %s", settings.chroma_collection_name)
            except Exception as e2:
                logger.error("ChromaDB 集合重建也失败: %s", e2)
                return None
    
    return _collection


def get_langchain_vector_store():
    """获取 LangChain Chroma 向量存储实例"""
    settings = get_settings()
    embeddings = get_embeddings()
    if embeddings is None:
        return None
    try:
        from langchain_chroma import Chroma
        return Chroma(
            collection_name=settings.chroma_collection_name,
            embedding_function=embeddings,
            persist_directory=settings.chroma_persist_dir,
        )
    except Exception as e:
        logger.error("获取 LangChain VectorStore 失败: %s", e)
        return None


async def add_document_chunks(
    kb_id: str,
    doc_id: str,
    filename: str,
    chunks: list[str],
    metadatas: Optional[list[dict]] = None,
) -> int:
    """
    将文档分块添加到 ChromaDB
    
    Args:
        kb_id: 知识库 ID
        doc_id: 文档 ID
        filename: 文件名
        chunks: 文本分块列表
        metadatas: 元数据列表（可选）
        
    Returns:
        添加的分块数量
    """
    try:
        collection = get_collection()
        if collection is None:
            logger.warning("ChromaDB 集合不可用，跳过文档索引: %s", filename)
            return 0
        
        # 准备 ID 和元数据
        ids = []
        documents = []
        metas = []
        
        for i, chunk in enumerate(chunks):
            chunk_id = f"kd_{doc_id}_chunk_{i:04d}"
            ids.append(chunk_id)
            documents.append(chunk)
            
            meta = {
                "kb_id": kb_id,
                "doc_id": doc_id,
                "filename": filename,
                "chunk_index": i,
            }
            if metadatas and i < len(metadatas):
                meta.update(metadatas[i])
            metas.append(meta)
        
        # 使用原生 ChromaDB 批量添加
        if hasattr(collection, "_collection"):
            # LangChain Chroma 包装
            collection.add_documents(
                documents=[
                    __import__("langchain_core.documents", fromlist=["Document"]).Document(
                        page_content=chunk, metadata=meta
                    )
                    for chunk, meta in zip(documents, metas)
                ]
            )
        else:
            # 原生 ChromaDB
            collection.add(
                ids=ids,
                documents=documents,
                metadatas=metas,
            )
        
        logger.info("✅ 已添加 %d 个分块到 ChromaDB (doc: %s)", len(chunks), doc_id)
        return len(chunks)
    
    except Exception as e:
        logger.error("ChromaDB 添加分块失败: %s", e)
        return 0


async def delete_document_chunks(doc_id: str) -> bool:
    """
    从 ChromaDB 删除指定文档的所有分块
    
    Args:
        doc_id: 文档 ID
        
    Returns:
        是否成功
    """
    try:
        collection = get_collection()
        
        if hasattr(collection, "_collection"):
            # LangChain Chroma
            collection.delete(where={"doc_id": doc_id})
        else:
            # 原生 ChromaDB
            collection.delete(where={"doc_id": doc_id})
        
        logger.info("✅ 已删除文档 %s 的所有分块", doc_id)
        return True
    except Exception as e:
        logger.error("ChromaDB 删除分块失败: %s", e)
        return False


async def delete_kb_chunks(kb_id: str) -> bool:
    """
    从 ChromaDB 删除指定知识库的所有分块
    
    Args:
        kb_id: 知识库 ID
        
    Returns:
        是否成功
    """
    try:
        collection = get_collection()
        collection.delete(where={"kb_id": kb_id})
        logger.info("✅ 已删除知识库 %s 的所有分块", kb_id)
        return True
    except Exception as e:
        logger.error("ChromaDB 删除知识库分块失败: %s", e)
        return False


async def search_similar_chunks(
    query: str,
    kb_id: str,
    k: int = 5,
) -> list[dict]:
    """
    从知识库中检索与查询最相似的分块
    
    Args:
        query: 查询文本
        kb_id: 知识库 ID
        k: 返回结果数
        
    Returns:
        检索结果列表，每项包含 text, metadata, score
    """
    try:
        # 方案 1：使用 LangChain 检索（自动 Embedding，需 HuggingFace 模型）
        vector_store = get_langchain_vector_store()
        if vector_store:
            retriever = vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": k, "filter": {"kb_id": kb_id}},
            )
            results = retriever.invoke(query)
            return [
                {
                    "text": doc.page_content,
                    "metadata": doc.metadata,
                    "score": getattr(doc, "score", 0),
                }
                for doc in results
            ]
        
        # 方案 2：使用原生 ChromaDB query_texts（自动使用 ChromaDB 内置 embedding）
        collection = get_collection()
        if collection is None:
            logger.warning("ChromaDB 集合不可用")
            return []
        
        # 检查是否是原生 ChromaDB 集合（没有 LangChain 包装）
        if not hasattr(collection, "_collection"):
            results = collection.query(
                query_texts=[query],
                n_results=k,
                where={"kb_id": kb_id},
                include=["documents", "metadatas", "distances"],
            )
            
            docs = []
            if results["documents"] and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    docs.append({
                        "text": doc,
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "score": 1 - results["distances"][0][i] if results["distances"] else 0,
                    })
            return docs
        
        # 方案 3：LangChain Chroma 包装 + 手动 Embedding 查询
        from app.services.embedding_service import embed_query
        
        query_vector = await embed_query(query)
        if query_vector is None:
            logger.warning("Embedding 模型不可用，无法进行向量检索")
            return []
        
        results = collection._collection.query(
            query_embeddings=[query_vector],
            n_results=k,
            where={"kb_id": kb_id},
            include=["documents", "metadatas", "distances"],
        )
        
        docs = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                docs.append({
                    "text": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "score": 1 - results["distances"][0][i] if results["distances"] else 0,
                })
        return docs
    
    except Exception as e:
        logger.error("向量检索失败: %s", e)
        return []


async def get_chroma_collection_stats() -> dict:
    """获取 ChromaDB 集合统计信息"""
    try:
        collection = get_collection()
        count = collection.count()
        return {"total_chunks": count}
    except Exception as e:
        logger.error("获取 ChromaDB 统计失败: %s", e)
        return {"total_chunks": 0}
