from fastapi import APIRouter, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select
from datetime import datetime

from app.auth.decorators import require_admin
from app.internal.db import engine
from app.models.prompt import AIPromptTemplate, PromptType
from app.routers.admin import templates as shared_templates

router = APIRouter(prefix="/admin", tags=["prompt_template"])
templates: Jinja2Templates = shared_templates


@router.get("/prompt-template", response_class=HTMLResponse)
async def get_prompt_template_config(request: Request, current_user: dict = Depends(require_admin())):
    """提示词模板配置（单条）页面"""
    with Session(engine) as session:
        tpl = session.exec(select(AIPromptTemplate)).first()
        if not tpl:
            tpl = AIPromptTemplate(
                name="默认模板",
                prompt_type=PromptType.PRODUCT_ARTICLE,
                prompt_template="",
                is_active=True,
                platform="xhs",
                created_by=current_user.get("username"),
                owner_id="system",
            )
            session.add(tpl)
            session.commit()
            session.refresh(tpl)
        return templates.TemplateResponse(
            "admin/prompt_template_config.html",
            {
                "request": request,
                "user": current_user,
                "tpl": tpl,
            },
        )


@router.post("/prompt-template")
async def save_prompt_template(
    request: Request,
    name: str = Form(...),
    prompt_type: PromptType = Form(...),
    prompt_template: str = Form(...),
    is_active: bool = Form(False),
    platform: str = Form("xhs"),
    current_user: dict = Depends(require_admin()),
):
    """创建或更新提示词模板"""
    with Session(engine) as session:
        tpl = session.exec(select(AIPromptTemplate).limit(1)).first()
        if not tpl:
            tpl = AIPromptTemplate(created_by=current_user.get("username"), owner_id="system")
            session.add(tpl)

        tpl.name = name
        tpl.prompt_type = prompt_type
        tpl.prompt_template = prompt_template
        tpl.is_active = is_active
        tpl.platform = platform

        session.commit()

        if request.headers.get("accept") == "application/json":
            return JSONResponse({"status": "success"})
        return RedirectResponse(url="/admin/prompt-template", status_code=302)


@router.post("/prompt-template/toggle")
async def toggle_prompt_template(current_user: dict = Depends(require_admin())):
    """启用/停用模板（单条）"""
    with Session(engine) as session:
        tpl = session.exec(select(AIPromptTemplate).limit(1)).first()
        if not tpl:
            raise HTTPException(status_code=404, detail="模板不存在")
        tpl.is_active = not tpl.is_active
        session.commit()
        return JSONResponse({"status": "success", "is_active": tpl.is_active}) 