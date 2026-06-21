"""JWT 工具模块 - Token 签发、验证、依赖注入"""

from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import get_settings

security = HTTPBearer(auto_error=False)


def create_token(user_id: str, openid: str) -> tuple[str, int]:
    """
    签发 JWT Token

    Args:
        user_id: 用户 ID
        openid: 微信 openid

    Returns:
        (token, expires_in_seconds)
    """
    settings = get_settings()
    expire_days = settings.jwt_expire_days
    expire_seconds = expire_days * 24 * 60 * 60

    payload = {
        "sub": user_id,
        "openid": openid,
        "type": "access",
        "iat": int(datetime.now(timezone.utc).timestamp()),
        "exp": int(datetime.now(timezone.utc).timestamp() + expire_seconds),
    }

    token = jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    return token, expire_seconds


def verify_token(token: str) -> dict:
    """
    验证 JWT Token

    Args:
        token: JWT 字符串

    Returns:
        解码后的 payload

    Raises:
        HTTPException: Token 无效或过期
    """
    settings = get_settings()
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 已过期，请重新登录",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的 Token",
        )


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> str:
    """
    从请求中解析当前用户 ID（依赖注入）

    Args:
        credentials: HTTP Authorization header

    Returns:
        user_id

    Raises:
        HTTPException: 未提供 Token 或 Token 无效
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少认证 Token",
        )

    payload = verify_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 中缺少用户信息",
        )

    return user_id
