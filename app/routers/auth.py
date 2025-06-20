"""
认证路由
提供用户注册、登录、登出等功能
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import RedirectResponse
from sqlmodel import Session, select
from typing import Optional

from app.auth.config import (
    fastapi_users,
    cookie_auth_backend,
    bearer_auth_backend,
    current_active_user,
    get_jwt_strategy
)
from app.auth.dependencies import require_super_admin
from app.models.user import User, UserCreate, UserRead, UserUpdate
from app.internal.db import engine

router = APIRouter()

# 包含 FastAPI-Users 的认证路由
router.include_router(
    fastapi_users.get_auth_router(cookie_auth_backend),
    prefix="/auth/cookie",
    tags=["auth"],
)

router.include_router(
    fastapi_users.get_auth_router(bearer_auth_backend),
    prefix="/auth/bearer",
    tags=["auth"],
)

# 用户注册路由（仅超级管理员可用）
router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
    dependencies=[Depends(require_super_admin)],
)

# 用户管理路由（仅超级管理员可用）
router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(require_super_admin)],
)


@router.get("/auth/me", response_model=UserRead, tags=["auth"])
async def get_current_user(user: User = Depends(current_active_user)):
    """获取当前用户信息"""
    return user


@router.get("/users/list", tags=["users"])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_super_admin)
):
    """获取用户列表（仅超级管理员）"""
    with Session(engine) as session:
        query = select(User).offset(skip).limit(limit)
        users = session.exec(query).all()
        
        return {
            "users": [
                UserRead(
                    id=user.id,
                    email=user.email,
                    username=user.username,
                    full_name=user.full_name,
                    role=user.role,
                    is_active=user.is_active,
                    is_superuser=user.is_superuser,
                    is_verified=user.is_verified,
                    created_at=user.created_at,
                    last_login=user.last_login,
                ) for user in users
            ],
            "total": len(users)
        }

# 添加自定义登出路由
@router.get("/auth/cookie/logout")
async def logout(request: Request):
    """自定义登出处理，清除session并重定向到登录页面"""
    response = RedirectResponse(url="/admin/login?logged_out=true", status_code=302)
    
    # 清除session
    if hasattr(request, "session"):
        request.session.clear()
    
    # 清除认证cookie
    response.delete_cookie(
        "auth_token",
        domain=None,
        path="/",
        secure=False,  # 生产环境设为True
        httponly=True
    )
    
    return response 