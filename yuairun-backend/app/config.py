"""应用配置管理"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings
import os


# 获取 backend 目录的绝对路径
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENV_FILE = os.path.join(BACKEND_DIR, ".env")


class Settings(BaseSettings):
    """应用配置，从环境变量读取"""

    # DeepSeek API
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"

    # Tavily Search
    tavily_api_key: str = ""

    # FastAPI
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = True

    # CORS
    cors_origins: list[str] = ["*"]

    # Mock
    use_mock_llm: bool = True

    # JWT
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_expire_days: int = 30

    # MySQL
    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = ""
    mysql_database: str = "yuairundeep"

    # 微信小程序
    wx_appid: str = ""
    wx_secret: str = ""

    # Embedding & ChromaDB
    embedding_cache_dir: str = "./models_cache"
    chroma_persist_dir: str = "./chroma_data"

    # 知识库
    knowledge_base_dir: str = "./knowledge_base"

    # ChromaDB 集合名称
    chroma_collection_name: str = "yuairun_knowledge"

    model_config = {
        "env_file": ENV_FILE,
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 将相对路径转为基于 backend 目录的绝对路径
        if self.embedding_cache_dir and not os.path.isabs(self.embedding_cache_dir):
            self.embedding_cache_dir = os.path.abspath(
                os.path.join(BACKEND_DIR, self.embedding_cache_dir))
        if self.chroma_persist_dir and not os.path.isabs(self.chroma_persist_dir):
            self.chroma_persist_dir = os.path.abspath(
                os.path.join(BACKEND_DIR, self.chroma_persist_dir))
        if self.knowledge_base_dir and not os.path.isabs(self.knowledge_base_dir):
            self.knowledge_base_dir = os.path.abspath(
                os.path.join(BACKEND_DIR, self.knowledge_base_dir))


@lru_cache()
def get_settings() -> Settings:
    """获取单例配置实例"""
    return Settings()
