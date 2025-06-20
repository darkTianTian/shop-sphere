"""
用户认证配置
配置 FastAPI-Users 认证系统
"""

import os
from typing import Optional
from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    CookieTransport,
)
from fastapi_users.authentication.strategy.jwt import JWTStrategy
from fastapi_users_db_sqlmodel import SQLModelUserDatabase
from sqlmodel import Session

from app.internal.db import engine
from app.models.user import User, UserCreate


# JWT 配置
SECRET = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")


class UserManager(BaseUserManager[User, int]):
    """用户管理器"""
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        """用户注册后的回调"""
        print(f"用户 {user.email} 注册成功")

    async def on_after_login(
        self,
        user: User,
        request: Optional[Request] = None,
    ):
        """用户登录后的回调"""
        print(f"用户 {user.email} 登录成功")
        # 更新最后登录时间
        from datetime import datetime
        with Session(engine) as session:
            db_user = session.get(User, user.id)
            if db_user:
                db_user.last_login = datetime.now()
                session.commit()


async def get_user_db():
    """获取用户数据库会话"""
    with Session(engine) as session:
        yield SQLModelUserDatabase(session, User)


async def get_user_manager(user_db=Depends(get_user_db)):
    """获取用户管理器"""
    yield UserManager(user_db)


# Cookie 认证传输（用于网页）
cookie_transport = CookieTransport(
    cookie_name="auth_token",
    cookie_max_age=3600 * 24 * 7,  # 7天
    cookie_httponly=True,
    cookie_secure=False,  # 生产环境改为 True
)

# Bearer Token 认证传输（用于API）
bearer_transport = BearerTransport(tokenUrl="auth/bearer/login")

# JWT 认证策略
def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(
        secret=SECRET,
        lifetime_seconds=3600 * 24 * 7,  # 7天
    )

# 认证后端
cookie_auth_backend = AuthenticationBackend(
    name="cookie",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,
)

bearer_auth_backend = AuthenticationBackend(
    name="bearer",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

# FastAPI Users 实例
fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [cookie_auth_backend, bearer_auth_backend],
)

# 依赖项
current_active_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True) 