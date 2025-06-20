"""
管理页面路由
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from app.auth.config import current_superuser, fastapi_users
from app.internal.db import engine
from app.models.user import User, UserRole

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
async def admin_home(request: Request, user: Optional[User] = Depends(current_superuser)):
    """管理后台首页"""
    if not user:
        return RedirectResponse(url="/admin/login")
    return templates.TemplateResponse(
        "admin/base.html",
        {"request": request, "user": user}
    )


@router.get("/users", response_class=HTMLResponse)
async def list_users(
    request: Request,
    user: User = Depends(current_superuser),
):
    """用户列表页面"""
    with Session(engine) as session:
        users = session.exec(select(User)).all()
        return templates.TemplateResponse(
            "admin/users.html",
            {"request": request, "user": user, "users": users}
        )


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(current_superuser),
):
    """删除用户"""
    if user_id == current_user.id:
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