"""数据库连接与会话管理 - SQLAlchemy 2.0 + aiomysql 异步模式"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import get_settings


class Base(DeclarativeBase):
    """SQLAlchemy ORM 基类"""
    pass


def get_database_url() -> str:
    """
    从配置构建异步 MySQL 连接 URL

    Returns:
        异步数据库 URL (mysql+aiomysql://...)
    """
    settings = get_settings()
    return (
        f"mysql+aiomysql://{settings.mysql_user}:{settings.mysql_password}"
        f"@{settings.mysql_host}:{settings.mysql_port}/{settings.mysql_database}"
        f"?charset=utf8mb4"
    )


# 全局引擎和会话工厂（在 lifespan 中初始化）
_engine = None
_session_maker = None


async def init_db():
    """
    初始化数据库引擎，自动创建所有表

    在应用启动时调用
    """
    global _engine, _session_maker
    database_url = get_database_url()
    _engine = create_async_engine(database_url, echo=False, pool_pre_ping=True)
    _session_maker = async_sessionmaker(_engine, expire_on_commit=False)

    # 自动创建表
    async with _engine.begin() as conn:
        from app.db.models import Base as ModelsBase
        await conn.run_sync(ModelsBase.metadata.create_all)

    print(f"✅ 数据库连接成功: {get_database_url()}")


async def close_db():
    """
    关闭数据库引擎

    在应用关闭时调用
    """
    global _engine
    if _engine:
        await _engine.dispose()
        print("✅ 数据库连接已关闭")


async def get_session() -> AsyncSession:
    """
    获取数据库会话（用于依赖注入）

    Yields:
        AsyncSession 实例
    """
    if _session_maker is None:
        raise RuntimeError("数据库未初始化，请先调用 init_db()")

    async with _session_maker() as session:
        try:
            yield session
        finally:
            await session.close()
