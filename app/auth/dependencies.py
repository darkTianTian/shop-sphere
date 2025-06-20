"""
权限检查依赖项
提供基于角色的权限控制
"""

from functools import wraps
from typing import Callable
from fastapi import Depends, HTTPException, status
from app.auth.config import current_active_user
from app.models.user import User, UserRole, has_permission


def require_role(required_role: UserRole):
    """要求特定角色的装饰器"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 从 kwargs 中获取用户
            user = kwargs.get('current_user')
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="需要登录"
                )
            
            # 检查角色权限
            role_hierarchy = {
                UserRole.VIEWER: 1,
                UserRole.EDITOR: 2,
                UserRole.ADMIN: 3,
                UserRole.SUPER_ADMIN: 4
            }
            
            user_level = role_hierarchy.get(user.role, 0)
            required_level = role_hierarchy.get(required_role, 0)
            
            if user_level < required_level:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="权限不足"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def require_permission(resource: str, action: str):
    """要求特定权限的装饰器"""
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            user = kwargs.get('current_user')
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="需要登录"
                )
            
            if not has_permission(user.role, resource, action):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"没有权限执行 {action} 操作在 {resource} 资源上"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


# 常用的权限依赖项
async def require_admin_user(current_user: User = Depends(current_active_user)):
    """要求管理员权限"""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限"
        )
    return current_user


async def require_super_admin(current_user: User = Depends(current_active_user)):
    """要求超级管理员权限"""
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要超级管理员权限"
        )
    return current_user


def check_resource_permission(resource: str, action: str):
    """检查资源权限的依赖项工厂"""
    async def permission_checker(current_user: User = Depends(current_active_user)):
        if not has_permission(current_user.role, resource, action):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"没有权限执行 {action} 操作在 {resource} 资源上"
            )
        return current_user
    return permission_checker


# 预定义的权限检查器
require_product_read = check_resource_permission("products", "read")
require_product_write = check_resource_permission("products", "create")
require_product_update = check_resource_permission("products", "update")
require_product_delete = check_resource_permission("products", "delete")

require_article_read = check_resource_permission("articles", "read")
require_article_write = check_resource_permission("articles", "create")
require_article_update = check_resource_permission("articles", "update")
require_article_delete = check_resource_permission("articles", "delete")

require_user_read = check_resource_permission("users", "read")
require_user_write = check_resource_permission("users", "create")
require_user_update = check_resource_permission("users", "update")
require_user_delete = check_resource_permission("users", "delete") 