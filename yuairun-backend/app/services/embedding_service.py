"""Embedding 模型服务 — 文本向量化（支持降级和子进程安全加载）"""

import logging
from app.config import get_settings

logger = logging.getLogger(__name__)

# 全局缓存和标记
_embeddings_instance = None  # 缓存 Embedding 模型实例
_embedding_available = True  # 是否可加载 Embedding 模型


def _verify_load_safe(settings):
    """在子进程中验证模型可加载（模块级函数，支持 pickle）"""
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
        test_model = HuggingFaceEmbeddings(
            model_name="BAAI/bge-m3",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
            cache_folder=settings.embedding_cache_dir,
        )
        test_model.embed_query("验证")
    except Exception:
        pass


def get_embeddings():
    """
    获取 Embedding 模型实例（单例，手动缓存）
    
    使用 BAAI/bge-m3 模型（中英双语，1024 维向量）。
    如果模型加载失败，打印警告并返回 None（调用方处理降级）。
    """
    global _embeddings_instance, _embedding_available

    if _embeddings_instance is not None:
        return _embeddings_instance
    if not _embedding_available:
        return None

    settings = get_settings()
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
        import os

        # 快速检查：模型文件是否已完整下载
        model_dir = os.path.join(settings.embedding_cache_dir, "models--BAAI--bge-m3")
        has_blobs = os.path.isdir(model_dir) and any(
            f.endswith(".safetensors") or f.endswith(".bin")
            for _, _, files in os.walk(model_dir) for f in files
        )
        if not has_blobs:
            logger.warning("⚠️ BGE-M3 模型文件未找到，跳过加载（需先下载）")
            _embedding_available = False
            return None

        # 直接加载模型（模型文件已在缓存中，跳过子进程验证以避免阻塞事件循环）
        _embeddings_instance = HuggingFaceEmbeddings(
            model_name="BAAI/bge-m3",
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
            cache_folder=settings.embedding_cache_dir,
        )
        _embeddings_instance.embed_query("验证")  # 快速测试
        logger.info("✅ BGE-M3 Embedding 模型加载成功 (1024维)")
        return _embeddings_instance

    except ImportError:
        logger.warning("⚠️ langchain-huggingface 未安装，无法加载 Embedding 模型")
        _embedding_available = False
        return None
    except Exception as e:
        logger.warning("⚠️ Embedding 模型加载失败: %s", e)
        _embedding_available = False
        return None


async def embed_texts(texts: list[str]) -> list[list[float]] | None:
    """将文本列表转为向量"""
    embeddings = get_embeddings()
    if embeddings is None:
        return None
    try:
        return embeddings.embed_documents(texts)
    except Exception as e:
        logger.error("Embedding 生成失败: %s", e)
        return None


async def embed_query(text: str) -> list[float] | None:
    """将查询文本转为向量"""
    embeddings = get_embeddings()
    if embeddings is None:
        return None
    try:
        return embeddings.embed_query(text)
    except Exception as e:
        logger.error("查询 Embedding 生成失败: %s", e)
        return None
