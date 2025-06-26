from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from datetime import time

from app.auth.decorators import require_admin
from app.internal.db import engine
from app.models.publish_config import PublishConfig
from app.routers.admin import templates as shared_templates

router = APIRouter(prefix="/admin", tags=["publish_config"])
templates: Jinja2Templates = shared_templates

@router.get("/publish-config", response_class=HTMLResponse)
async def get_publish_config(request: Request, current_user: dict = Depends(require_admin())):
    """发布配置页面"""
    with Session(engine) as session:
        # 获取当前配置，如果不存在则创建默认配置
        config = session.exec(select(PublishConfig)).first()
        if not config:
            config = PublishConfig()
            session.add(config)
            session.commit()
            session.refresh(config)
        
        return templates.TemplateResponse(
            "admin/publish_config.html",
            {
                "request": request,
                "user": current_user,
                "config": config,
            }
        )

@router.post("/publish-config")
async def update_publish_config(
    request: Request,
    generate_hour: int = Form(...),
    generate_minute: int = Form(...),
    publish_start_hour: int = Form(...),
    publish_start_minute: int = Form(...),
    publish_end_hour: int = Form(...),
    publish_end_minute: int = Form(...),
    daily_publish_limit: int = Form(...),
    is_enabled: bool = Form(False),
    current_user: dict = Depends(require_admin())
):
    """更新发布配置"""
    try:
        with Session(engine) as session:
            config = session.exec(select(PublishConfig)).first()
            if not config:
                config = PublishConfig()
                session.add(config)
            
            # 更新配置
            config.generate_time = time(hour=generate_hour, minute=generate_minute)
            config.publish_start_time = time(hour=publish_start_hour, minute=publish_start_minute)
            config.publish_end_time = time(hour=publish_end_hour, minute=publish_end_minute)
            config.daily_publish_limit = daily_publish_limit
            config.is_enabled = is_enabled
            
            session.commit()
            
            # 根据请求的 Accept 头返回不同的响应
            if request.headers.get("accept") == "application/json":
                return JSONResponse(content={"status": "success", "message": "配置已保存"})
            else:
                return RedirectResponse(
                    url="/admin/publish-config",
                    status_code=302
                )
    except Exception as e:
        if request.headers.get("accept") == "application/json":
            return JSONResponse(
                status_code=500,
                content={"status": "error", "message": str(e)}
            )
        raise HTTPException(status_code=500, detail=str(e)) 