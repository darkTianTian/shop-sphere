from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select, func
import math
from datetime import datetime

from app.auth.decorators import require_admin
from app.internal.db import engine
from app.models.product import Product, ProductArticle, ArticleStatus, ArticleVideoMapping
from app.models.video import Video
from app.services.oss_service import OSSService
from app.routers.admin import templates as shared_templates

router = APIRouter(prefix="/admin", tags=["articles"])

templates: Jinja2Templates = shared_templates

@router.get("/articles", response_class=HTMLResponse)
async def list_articles(request: Request, page: int = 1, status: str | None = None, current_user: dict = Depends(require_admin())):
    PAGE_SIZE = 20
    page = max(page, 1)
    with Session(engine) as session:
        base_query = select(ProductArticle)
        if status and status in [s.value for s in ArticleStatus]:
            base_query = base_query.where(ProductArticle.status == ArticleStatus(status))

        total = session.exec(select(func.count()).select_from(base_query.subquery())).one()
        total_pages = max(math.ceil(total / PAGE_SIZE), 1)
        offset_val = (page - 1) * PAGE_SIZE
        articles = (
            session.exec(
                base_query.order_by(ProductArticle.create_at.desc()).offset(offset_val).limit(PAGE_SIZE)
            ).all()
        )
        
        # 获取商品信息
        item_ids = [a.item_id for a in articles if a.item_id]
        product_map: dict[str, Product] = {}
        if item_ids:
            products = session.exec(select(Product).where(Product.item_id.in_(item_ids))).all()
            product_map = {p.item_id: p for p in products}
        
        # 获取文章-视频关联信息
        article_ids = [a.id for a in articles]
        video_map = {}
        if article_ids:
            # 查询已发布的文章-视频关联记录
            mappings = session.exec(
                select(ArticleVideoMapping, Video)
                .join(Video, ArticleVideoMapping.video_id == Video.id, isouter=True)
                .where(
                    ArticleVideoMapping.article_id.in_(article_ids),
                )
            ).all()
            
            # 生成视频缩略图URL
            oss_service = OSSService()
            for mapping, video in mappings:
                if video and oss_service.is_available():
                    style = "video/snapshot,t_1000,f_jpg,w_320,m_fast"
                    thumb_url = oss_service.bucket.sign_url(
                        "GET", 
                        video.oss_object_key, 
                        3600, 
                        params={"x-oss-process": style}
                    )
                    video_map[mapping.article_id] = {
                        "video": video,
                        "thumb_url": thumb_url
                    }

        return templates.TemplateResponse(
            "admin/articles.html",
            {
                "request": request,
                "user": current_user,
                "articles": articles,
                "ArticleStatus": ArticleStatus,
                "product_map": product_map,
                "video_map": video_map,
                "page": page,
                "total_pages": total_pages,
                "has_prev": page > 1,
                "has_next": page < total_pages,
                "current_status": status or "",
                "all_statuses": [s.value for s in ArticleStatus],
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
        
        # 处理预发布时间
        try:
            pre_publish_time = int(form_data.get("pre_publish_time", "0"))
            article.pre_publish_time = pre_publish_time
        except ValueError:
            article.pre_publish_time = 0
        
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