"""
管理后台权限验证装饰器
"""
from typing import Optional, Callable, Any
from fastapi import Request, HTTPException, Depends
from fastapi.responses import RedirectResponse
from app.models.user import UserRole

def get_current_admin_user(
    request: Request,
    roles: Optional[list[UserRole]] = None
) -> dict[str, Any]:
    """
    获取当前管理后台用户
    :param request: FastAPI请求对象
    :param roles: 允许访问的角色列表
    :return: 用户信息字典
    """
    # 检查用户是否已登录
    user = request.session.get("user")
    if not user:
        if request.headers.get("accept") == "application/json":
            raise HTTPException(
                status_code=401,
                detail="需要登录"
            )
        raise HTTPException(
            status_code=307,  # 临时重定向
            detail="需要登录",
            headers={"Location": "/admin/login"}
        )
    
    # 如果指定了角色要求，检查用户角色
    if roles:
        user_role = UserRole(user.get("role", "viewer"))
        if user_role not in roles:
            # 对于API请求返回403错误
            if request.headers.get("accept") == "application/json":
                raise HTTPException(
                    status_code=403,
                    detail="权限不足"
                )
            # 对于页面请求重定向到首页
            raise HTTPException(
                status_code=307,  # 临时重定向
                detail="权限不足",
                headers={"Location": "/admin"}
            )
    
    return user

def require_admin(roles: Optional[list[UserRole]] = None) -> Callable:
    """管理后台权限验证依赖"""
    def dependency(request: Request) -> dict[str, Any]:
        return get_current_admin_user(request, roles)
    return dependency

def require_superuser() -> Callable:
    """超级管理员权限验证依赖"""
    def dependency(request: Request) -> dict[str, Any]:
        return get_current_admin_user(request, [UserRole.SUPER_ADMIN])
    return dependency

def require_admin_or_superuser() -> Callable:
    """管理员或超级管理员权限验证依赖"""
    def dependency(request: Request) -> dict[str, Any]:
        return get_current_admin_user(request, [UserRole.ADMIN, UserRole.SUPER_ADMIN])
    return dependency 