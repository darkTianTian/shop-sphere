"""
用户模型
包含用户认证和权限管理
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from fastapi_users import schemas
from sqlmodel import SQLModel, Field
import sqlalchemy as sa


class UserRole(str, Enum):
    """用户角色枚举"""
    SUPER_ADMIN = "super_admin"  # 超级管理员
    ADMIN = "admin"              # 管理员
    EDITOR = "editor"            # 编辑
    VIEWER = "viewer"            # 查看者


class User(SQLModel, table=True):
    """用户表"""
    __tablename__ = "users"
    
    # FastAPI-Users 必需字段
    id: int = Field(default=None, primary_key=True)
    email: str = Field(max_length=320, unique=True, index=True)
    hashed_password: str = Field(max_length=1024)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    is_verified: bool = Field(default=False)
    
    # 扩展字段
    username: str = Field(max_length=50, unique=True, index=True, description="用户名")
    full_name: Optional[str] = Field(default=None, max_length=100, description="真实姓名")
    role: UserRole = Field(default=UserRole.VIEWER, description="用户角色")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    last_login: Optional[datetime] = Field(default=None, description="最后登录时间")


class UserCreate(schemas.CreateUpdateDictModel):
    """用户创建模型"""
    email: str = Field(max_length=320, description="邮箱")
    username: str = Field(max_length=50, description="用户名")
    full_name: Optional[str] = Field(default=None, max_length=100, description="真实姓名")
    password: str = Field(min_length=6, description="密码")
    role: UserRole = Field(default=UserRole.VIEWER, description="用户角色")


class UserRead(schemas.BaseUser[int]):
    """用户读取模型"""
    username: str
    full_name: Optional[str]
    role: UserRole
    created_at: datetime
    last_login: Optional[datetime]


class UserUpdate(schemas.BaseUserUpdate):
    """用户更新模型"""
    username: Optional[str] = Field(default=None, max_length=50)
    full_name: Optional[str] = Field(default=None, max_length=100)
    role: Optional[UserRole] = None


# 权限级别定义
ROLE_PERMISSIONS = {
    UserRole.SUPER_ADMIN: {
        "users": ["create", "read", "update", "delete"],
        "products": ["create", "read", "update", "delete"],
        "articles": ["create", "read", "update", "delete"],
        "tags": ["create", "read", "update", "delete"],
        "prompts": ["create", "read", "update", "delete"],
        "system": ["config", "logs"]
    },
    UserRole.ADMIN: {
        "users": ["read"],
        "products": ["create", "read", "update", "delete"],
        "articles": ["create", "read", "update", "delete"],
        "tags": ["create", "read", "update", "delete"],
        "prompts": ["read", "update"]
    },
    UserRole.EDITOR: {
        "products": ["read"],
        "articles": ["create", "read", "update"],
        "tags": ["read"],
        "prompts": ["read"]
    },
    UserRole.VIEWER: {
        "products": ["read"],
        "articles": ["read"],
        "tags": ["read"],
        "prompts": ["read"]
    }
}


def has_permission(user_role: UserRole, resource: str, action: str) -> bool:
    """检查用户是否有指定权限"""
    permissions = ROLE_PERMISSIONS.get(user_role, {})
    resource_permissions = permissions.get(resource, [])
    return action in resource_permissions 