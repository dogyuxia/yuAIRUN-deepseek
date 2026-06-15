"""健康检查端点"""

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/api/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "service": "yuAIRUN Backend",
        "version": "1.0.0",
    }
