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

    # FastAPI
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    debug: bool = True

    # CORS
    cors_origins: list[str] = ["*"]

    # Mock
    use_mock_llm: bool = True

    model_config = {
        "env_file": ENV_FILE,
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    """获取单例配置实例"""
    return Settings()
