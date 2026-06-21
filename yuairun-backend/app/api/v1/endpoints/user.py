"""用户系统 API 路由"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.models.user import (
    LoginRequest,
    RefreshTokenRequest,
    UpdateProfileRequest,
    HistorySyncRequest,
    WrongBookSyncRequest,
    ApiResponse,
)
from app.services.user_service import (
    login_or_register,
    get_user_profile,
    update_user_profile,
    get_history_list,
    get_history_detail,
    sync_history_records,
    get_wrong_book,
    sync_wrong_book,
    mark_wrong_book_mastered,
    delete_wrong_book,
)
from app.utils.auth import verify_token, create_token, security

router = APIRouter(prefix="/api/user", tags=["user"])


# ============================================================
# 依赖：从 Authorization header 解析用户 ID
# ============================================================

async def require_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> str:
    """
    要求用户已认证

    从 Authorization header 解析用户 ID
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少认证 Token",
        )

    try:
        payload = verify_token(credentials.credentials)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token 中缺少用户信息",
            )
        return user_id
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token 验证失败: {str(e)}",
        )


# ============================================================
# P0: 登录认证
# ============================================================

@router.post("/login")
async def login(request: LoginRequest, db: AsyncSession = Depends(get_session)):
    """微信登录/注册"""
    try:
        data = await login_or_register(
            db,
            code=request.code,
            nickname=request.nickname,
            avatar_url=request.avatarUrl,
        )
        return ApiResponse(success=True, data=data)
    except Exception as e:
        return ApiResponse(success=False, error=f"登录失败: {str(e)}")


@router.post("/refresh-token")
async def refresh_token(request: RefreshTokenRequest, db: AsyncSession = Depends(get_session)):
    """刷新 Token"""
    try:
        # 验证旧 Token
        payload = verify_token(request.token)
        user_id = payload.get("sub")
        openid = payload.get("openid")

        new_token, expires_in = create_token(user_id, openid)

        data = {
            "token": new_token,
            "expiresIn": expires_in,
        }
        return ApiResponse(success=True, data=data)
    except HTTPException:
        raise
    except Exception as e:
        return ApiResponse(success=False, error=f"刷新 Token 失败: {str(e)}")


# ============================================================
# P1: 个人中心
# ============================================================

@router.get("/profile")
async def profile(
    user_id: str = Depends(require_auth),
    db: AsyncSession = Depends(get_session),
):
    """获取用户信息和统计"""
    try:
        data = await get_user_profile(db, user_id)
        return ApiResponse(success=True, data=data)
    except ValueError as e:
        return ApiResponse(success=False, error=str(e))
    except Exception as e:
        return ApiResponse(success=False, error=f"获取用户信息失败: {str(e)}")


@router.put("/profile")
async def update_profile(
    request: UpdateProfileRequest,
    user_id: str = Depends(require_auth),
    db: AsyncSession = Depends(get_session),
):
    """更新用户信息"""
    try:
        data = await update_user_profile(db, user_id, nickname=request.nickname)
        return ApiResponse(success=True, data=data)
    except ValueError as e:
        return ApiResponse(success=False, error=str(e))
    except Exception as e:
        return ApiResponse(success=False, error=f"更新用户信息失败: {str(e)}")


# ============================================================
# P2: 闯关历史
# ============================================================

@router.get("/history")
async def history_list(
    page: int = Query(default=1, ge=1, description="页码"),
    pageSize: int = Query(default=20, ge=1, le=100, description="每页数量"),
    user_id: str = Depends(require_auth),
    db: AsyncSession = Depends(get_session),
):
    """分页获取闯关历史"""
    try:
        data = await get_history_list(db, user_id, page=page, page_size=pageSize)
        return ApiResponse(success=True, data=data)
    except Exception as e:
        return ApiResponse(success=False, error=f"获取闯关历史失败: {str(e)}")


@router.get("/history/{history_id}")
async def history_detail(
    history_id: str,
    user_id: str = Depends(require_auth),
    db: AsyncSession = Depends(get_session),
):
    """获取单条闯关记录详情"""
    try:
        data = await get_history_detail(db, user_id, history_id)
        return ApiResponse(success=True, data=data)
    except ValueError as e:
        return ApiResponse(success=False, error=str(e))
    except Exception as e:
        return ApiResponse(success=False, error=f"获取闯关记录详情失败: {str(e)}")


@router.post("/history/sync")
async def history_sync(
    request: HistorySyncRequest,
    user_id: str = Depends(require_auth),
    db: AsyncSession = Depends(get_session),
):
    """批量同步闯关记录"""
    try:
        records = [r.model_dump(by_alias=True) for r in request.records]
        data = await sync_history_records(db, user_id, records)
        return ApiResponse(success=True, data=data)
    except Exception as e:
        return ApiResponse(success=False, error=f"同步闯关记录失败: {str(e)}")


# ============================================================
# P2: 错题本
# ============================================================

@router.get("/wrong-book")
async def wrong_book_list(
    page: int = Query(default=1, ge=1, description="页码"),
    pageSize: int = Query(default=20, ge=1, le=100, description="每页数量"),
    subject: str = Query(default=None, description="学科筛选"),
    user_id: str = Depends(require_auth),
    db: AsyncSession = Depends(get_session),
):
    """分页获取错题本"""
    try:
        data = await get_wrong_book(db, user_id, page=page, page_size=pageSize, subject=subject)
        return ApiResponse(success=True, data=data)
    except Exception as e:
        return ApiResponse(success=False, error=f"获取错题本失败: {str(e)}")


@router.post("/wrong-book/sync")
async def wrong_book_sync(
    request: WrongBookSyncRequest,
    user_id: str = Depends(require_auth),
    db: AsyncSession = Depends(get_session),
):
    """批量同步错题"""
    try:
        items = [i.model_dump(by_alias=True) for i in request.items]
        data = await sync_wrong_book(db, user_id, items)
        return ApiResponse(success=True, data=data)
    except Exception as e:
        return ApiResponse(success=False, error=f"同步错题失败: {str(e)}")


@router.put("/wrong-book/{wrong_id}/master")
async def wrong_book_master(
    wrong_id: str,
    user_id: str = Depends(require_auth),
    db: AsyncSession = Depends(get_session),
):
    """标记错题为已掌握"""
    try:
        data = await mark_wrong_book_mastered(db, user_id, wrong_id)
        return ApiResponse(success=True, data=data)
    except ValueError as e:
        return ApiResponse(success=False, error=str(e))
    except Exception as e:
        return ApiResponse(success=False, error=f"操作失败: {str(e)}")


@router.delete("/wrong-book/{wrong_id}")
async def wrong_book_delete(
    wrong_id: str,
    user_id: str = Depends(require_auth),
    db: AsyncSession = Depends(get_session),
):
    """从错题本删除"""
    try:
        data = await delete_wrong_book(db, user_id, wrong_id)
        return ApiResponse(success=True, data=data)
    except ValueError as e:
        return ApiResponse(success=False, error=str(e))
    except Exception as e:
        return ApiResponse(success=False, error=f"删除失败: {str(e)}")
