from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select, func
import math
from datetime import datetime

from app.auth.decorators import require_admin
from app.internal.db import engine
from app.models.product import Product, ProductArticle, ArticleStatus
from app.routers.admin import templates as shared_templates

router = APIRouter(prefix="/admin", tags=["articles"])

templates: Jinja2Templates = shared_templates

@router.get("/articles", response_class=HTMLResponse)
async def list_articles(request: Request, page: int = 1, current_user: dict = Depends(require_admin())):
    PAGE_SIZE = 30
    page = max(page, 1)
    with Session(engine) as session:
        total = session.exec(select(func.count(ProductArticle.id))).one()
        total_pages = max(math.ceil(total / PAGE_SIZE), 1)
        offset_val = (page - 1) * PAGE_SIZE
        articles = (
            session.exec(
                select(ProductArticle).order_by(ProductArticle.create_at.desc()).offset(offset_val).limit(PAGE_SIZE)
            ).all()
        )
        item_ids = [a.item_id for a in articles if a.item_id]
        product_map: dict[str, Product] = {}
        if item_ids:
            products = session.exec(select(Product).where(Product.item_id.in_(item_ids))).all()
            product_map = {p.item_id: p for p in products}
        return templates.TemplateResponse(
            "admin/articles.html",
            {
                "request": request,
                "user": current_user,
                "articles": articles,
                "ArticleStatus": ArticleStatus,
                "product_map": product_map,
                "page": page,
                "total_pages": total_pages,
                "has_prev": page > 1,
                "has_next": page < total_pages,
            },
        )


@router.delete("/articles/{article_id}")
async def delete_article(article_id: int, current_user: dict = Depends(require_admin())):
    with Session(engine) as session:
        article = session.get(ProductArticle, article_id)
        if not article:
            raise HTTPException(status_code=404, detail="文章不存在")
        session.delete(article)
        session.commit()
        return {"ok": True}


@router.get("/articles/{article_id}/edit", response_class=HTMLResponse)
async def edit_article_form(article_id: int, request: Request, current_user: dict = Depends(require_admin())):
    with Session(engine) as session:
        article = session.get(ProductArticle, article_id)
        if not article:
            raise HTTPException(status_code=404, detail="文章不存在")
        
        # 过滤掉 published 状态
        available_statuses = [s.value for s in ArticleStatus if s != ArticleStatus.PUBLISHED]
        
        return templates.TemplateResponse(
            "admin/article_form.html",
            {
                "request": request, 
                "user": current_user, 
                "article": article, 
                "statuses": available_statuses
            }
        )


@router.post("/articles/{article_id}/edit")
async def edit_article(article_id: int, request: Request, current_user: dict = Depends(require_admin())):
    form_data = await request.form()
    with Session(engine) as session:
        article = session.get(ProductArticle, article_id)
        if not article:
            raise HTTPException(status_code=404, detail="文章不存在")
            
        new_title = form_data.get("title", "").strip()
        if new_title and len(new_title) > 20:
            raise HTTPException(status_code=400, detail="标题长度不能超过20个字符")
        article.title = new_title or article.title
        
        new_content = form_data.get("content", "").strip()
        if new_content and len(new_content) > 1000:
            raise HTTPException(status_code=400, detail="内容长度不能超过1000个字符")
        article.content = new_content or article.content
        
        article.tags = form_data.get("tags", article.tags)
        
        status_str = form_data.get("status")
        if status_str:
            # 验证状态是否有效且不是published
            if status_str == ArticleStatus.PUBLISHED.value:
                raise HTTPException(status_code=400, detail="不能直接设置为已发布状态")
            if status_str in [s.value for s in ArticleStatus if s != ArticleStatus.PUBLISHED]:
                article.status = ArticleStatus(status_str)
            else:
                raise HTTPException(status_code=400, detail="无效的状态值")
                
        article.update_at = int(datetime.utcnow().timestamp() * 1000)
        session.commit()
        
    return RedirectResponse(url="/admin/articles", status_code=302) 