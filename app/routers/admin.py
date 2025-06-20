"""
管理页面路由
"""

from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select, func

from app.auth.config import current_superuser, fastapi_users
from app.auth.decorators import require_admin, require_superuser, require_admin_or_superuser
from app.internal.db import engine
from app.models.user import User, UserRole
from app.models.product import Product

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/login", response_class=HTMLResponse)
async def admin_login(request: Request):
    """管理后台登录页面"""
    return templates.TemplateResponse(
        "admin/login.html",
        {"request": request}
    )


@router.get("/", response_class=HTMLResponse)
async def admin_home(
    request: Request,
    current_user: dict = Depends(require_admin())
):
    """管理后台首页"""
    with Session(engine) as session:
        stats = {}
        recent_activities = []
        
        # 总商品数（所有人都可以看到）
        total_products = session.exec(select(func.count(Product.id))).first()
        stats["total_products"] = total_products or 0
        
        # 只有超级管理员可以看到总用户数和所有人的活动
        if current_user.get("role") == UserRole.SUPER_ADMIN.value:
            # 获取总用户数
            total_users = session.exec(select(func.count(User.id))).first()
            stats["total_users"] = total_users or 0
            
            # 获取所有用户的最近活动
            recent_logins = session.exec(
                select(User)
                .where(User.last_login != None)
                .order_by(User.last_login.desc())
                .limit(5)
            ).all()
            
            recent_activities = [
                {
                    "description": f"用户 {user.username} 登录了系统",
                    "time": user.last_login,
                    "type": "login"
                }
                for user in recent_logins
                if user.last_login
            ]
        else:
            # 非超级管理员只能看到自己的活动
            user = session.exec(
                select(User)
                .where(User.id == current_user.get("id"))
            ).first()
            
            if user and user.last_login:
                recent_activities = [
                    {
                        "description": "您上次登录系统",
                        "time": user.last_login,
                        "type": "self_login"
                    }
                ]
    
    return templates.TemplateResponse(
        "admin/home.html",
        {
            "request": request,
            "user": current_user,
            "stats": stats,
            "recent_activities": recent_activities,
            "is_superuser": current_user.get("role") == UserRole.SUPER_ADMIN.value
        }
    )


@router.get("/users", response_class=HTMLResponse)
async def list_users(
    request: Request,
    current_user: dict = Depends(require_superuser())
):
    """用户列表页面（仅超级管理员可访问）"""
    # 再次验证权限（双重保险）
    if current_user.get("role") != UserRole.SUPER_ADMIN.value:
        return RedirectResponse(url="/admin")
    
    with Session(engine) as session:
        users = session.exec(select(User)).all()
        return templates.TemplateResponse(
            "admin/users.html",
            {"request": request, "user": current_user, "users": users}
        )


@router.get("/users/create", response_class=HTMLResponse)
async def create_user_form(
    request: Request,
    current_user: dict = Depends(require_superuser())
):
    """创建用户表单页面（仅超级管理员可访问）"""
    if current_user.get("role") != UserRole.SUPER_ADMIN.value:
        return RedirectResponse(url="/admin")
    
    return templates.TemplateResponse(
        "admin/users_form.html",
        {
            "request": request,
            "user": current_user,
            "roles": [role.value for role in UserRole],
            "target_user": None
        }
    )


@router.post("/users/create")
async def create_user(
    request: Request,
    current_user: dict = Depends(require_superuser())
):
    """创建用户处理（仅超级管理员可访问）"""
    if current_user.get("role") != UserRole.SUPER_ADMIN.value:
        raise HTTPException(status_code=403, detail="没有权限执行此操作")
    
    form_data = await request.form()
    
    # 验证必填字段
    required_fields = ["email", "username", "password", "role"]
    for field in required_fields:
        if not form_data.get(field):
            raise HTTPException(
                status_code=400,
                detail=f"字段 {field} 不能为空"
            )
    
    with Session(engine) as session:
        # 检查邮箱是否已存在
        existing_user = session.exec(
            select(User).where(User.email == form_data["email"])
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="该邮箱已被注册"
            )
        
        # 检查用户名是否已存在
        existing_user = session.exec(
            select(User).where(User.username == form_data["username"])
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="该用户名已被使用"
            )
        
        # 创建新用户
        new_user = User(
            email=form_data["email"],
            username=form_data["username"],
            role=UserRole(form_data["role"]),
            is_active=True,
            is_verified=True,
            is_superuser=form_data["role"] == UserRole.SUPER_ADMIN.value,
            hashed_password=""  # 临时值，会被set_password覆盖
        )
        new_user.set_password(form_data["password"])
        
        session.add(new_user)
        session.commit()
        session.refresh(new_user)
    
    return RedirectResponse(
        url="/admin/users",
        status_code=302
    )


@router.get("/users/{user_id}/edit", response_class=HTMLResponse)
async def edit_user_form(
    user_id: int,
    request: Request,
    current_user: dict = Depends(require_superuser())
):
    """编辑用户表单页面（仅超级管理员可访问）"""
    if current_user.get("role") != UserRole.SUPER_ADMIN.value:
        return RedirectResponse(url="/admin")
    
    with Session(engine) as session:
        target_user = session.get(User, user_id)
        if not target_user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        return templates.TemplateResponse(
            "admin/users_form.html",
            {
                "request": request,
                "user": current_user,
                "roles": [role.value for role in UserRole],
                "target_user": target_user
            }
        )


@router.post("/users/{user_id}/edit")
async def edit_user(
    user_id: int,
    request: Request,
    current_user: dict = Depends(require_superuser())
):
    """编辑用户处理（仅超级管理员可访问）"""
    if current_user.get("role") != UserRole.SUPER_ADMIN.value:
        raise HTTPException(status_code=403, detail="没有权限执行此操作")
    
    form_data = await request.form()
    
    with Session(engine) as session:
        target_user = session.get(User, user_id)
        if not target_user:
            raise HTTPException(status_code=404, detail="用户不存在")
        
        # 不允许编辑自己的角色和状态
        if user_id == current_user.get("id"):
            raise HTTPException(status_code=400, detail="不能修改自己的角色和状态")
        
        # 检查用户名是否已被其他用户使用
        if form_data["username"] != target_user.username:
            existing_user = session.exec(
                select(User).where(
                    User.username == form_data["username"],
                    User.id != user_id
                )
            ).first()
            if existing_user:
                raise HTTPException(
                    status_code=400,
                    detail="该用户名已被使用"
                )
        
        # 更新用户信息
        target_user.username = form_data["username"]
        target_user.role = UserRole(form_data["role"])
        target_user.is_superuser = form_data["role"] == UserRole.SUPER_ADMIN.value
        
        # 更新激活状态
        target_user.is_active = form_data.get("is_active") == "true"
        
        # 如果提供了新密码则更新密码
        if new_password := form_data.get("password"):
            if len(new_password) >= 6:
                target_user.set_password(new_password)
            else:
                raise HTTPException(status_code=400, detail="密码长度必须大于6位")
        
        session.commit()
    
    return RedirectResponse(
        url="/admin/users",
        status_code=302
    )


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: dict = Depends(require_superuser())
):
    """删除用户（仅超级管理员可访问）"""
    if current_user.get("role") != UserRole.SUPER_ADMIN.value:
        raise HTTPException(status_code=403, detail="没有权限执行此操作")
    
    if user_id == current_user.get("id"):
        raise HTTPException(status_code=400, detail="不能删除当前用户")
    
    with Session(engine) as session:
        user = session.get(User, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")
        if user.is_superuser:
            raise HTTPException(status_code=400, detail="不能删除超级管理员")
        session.delete(user)
        session.commit()
        return {"ok": True} 