"""FastAPI 应用入口"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.api.v1.endpoints import health, quiz, user, knowledge, document
from app.db.session import init_db, close_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    settings = get_settings()
    if settings.use_mock_llm:
        print("🔧 使用 Mock LLM 模式（测试用）")
    else:
        print("🤖 使用 DeepSeek API 模式")

    # 初始化数据库
    try:
        await init_db()
    except Exception as e:
        print(f"⚠️ 数据库初始化失败（可忽略，Mock 模式正常运行）: {e}")

    # 初始化系统知识库（无论 mock 模式都运行，因为不依赖 LLM）
    try:
        from app.services.knowledge_service import seed_system_knowledge_bases
        await seed_system_knowledge_bases()
    except Exception as e:
        print(f"⚠️ 系统知识库初始化失败: {e}")

    # 系统知识包文件索引（模型已缓存，直接同步执行）
    try:
        from app.services.knowledge_service import _index_system_markdown_files
        await _index_system_markdown_files()
    except Exception as e:
        print(f"⚠️ 系统知识包索引失败: {e}")

    print(f"📋 API 文档: http://localhost:{settings.app_port}/docs")
    yield

    # 关闭数据库
    await close_db()


def create_app() -> FastAPI:
    """创建 FastAPI 应用实例"""
    settings = get_settings()

    app = FastAPI(
        title="yuAIRUN Backend",
        description="AI 闯关学园后端 API",
        version="1.1.0",
        lifespan=lifespan,
    )

    # CORS 配置
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 注册路由
    app.include_router(health.router)
    app.include_router(quiz.router)
    app.include_router(user.router)
    app.include_router(knowledge.router)
    app.include_router(document.router)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug,
    )
