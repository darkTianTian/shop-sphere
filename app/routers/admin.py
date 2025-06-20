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
async def admin_home(request: Request):
    """管理后台首页"""
    # 从会话中获取用户信息
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/admin/login")
    
    with Session(engine) as session:
        # 获取统计数据
        total_users = session.exec(select(func.count(User.id))).first()
        total_products = session.exec(select(func.count(Product.id))).first()
        
        # 获取最近活动（这里示例使用最近的用户登录记录）
        recent_logins = session.exec(
            select(User)
            .where(User.last_login != None)
            .order_by(User.last_login.desc())
            .limit(5)
        ).all()
        
        recent_activities = [
            {
                "description": f"用户 {user.username} 登录了系统",
                "time": user.last_login
            }
            for user in recent_logins
            if user.last_login
        ]
        
        stats = {
            "total_users": total_users or 0,
            "total_products": total_products or 0,
        }
    
    return templates.TemplateResponse(
        "admin/home.html",
        {
            "request": request,
            "user": user,
            "stats": stats,
            "recent_activities": recent_activities
        }
    )


@router.get("/users", response_class=HTMLResponse)
async def list_users(request: Request):
    """用户列表页面"""
    # 从会话中获取用户信息
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/admin/login")
    
    # 检查是否是管理员
    if not user.get("is_superuser"):
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
    with Session(engine) as session:
        users = session.exec(select(User)).all()
        return templates.TemplateResponse(
            "admin/users.html",
            {"request": request, "user": user, "users": users}
        )


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    request: Request
):
    """删除用户"""
    # 从会话中获取用户信息
    current_user = request.session.get("user")
    if not current_user:
        raise HTTPException(status_code=401, detail="需要登录")
    
    # 检查是否是管理员
    if not current_user.get("is_superuser"):
        raise HTTPException(status_code=403, detail="需要管理员权限")
    
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