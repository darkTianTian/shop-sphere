from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select, func
import math
from datetime import datetime
import sqlalchemy as sa

from app.auth.decorators import require_admin
from app.internal.db import engine
from app.models.product import Product, ProductArticle, ArticleStatus, ArticleVideoMapping
from app.models.video import Video
from app.services.oss_service import OSSService
from app.routers.admin import templates as shared_templates

router = APIRouter(prefix="/admin", tags=["articles"])

templates: Jinja2Templates = shared_templates

@router.get("/articles", response_class=HTMLResponse)
async def list_articles(
    request: Request,
    page: int = 1,
    status: str | None = None,
    item_id: str | None = None,
    sort: str | None = None,
    dir: str = "desc",
    current_user: dict = Depends(require_admin()),
):
    PAGE_SIZE = 20
    page = max(page, 1)
    with Session(engine) as session:
        base_query = select(ProductArticle)
        if status and status in [s.value for s in ArticleStatus]:
            base_query = base_query.where(ProductArticle.status == ArticleStatus(status))

        if item_id:
            base_query = base_query.where(ProductArticle.item_id == item_id)

        total = session.exec(select(func.count()).select_from(base_query.subquery())).one()
        total_pages = max(math.ceil(total / PAGE_SIZE), 1)
        offset_val = (page - 1) * PAGE_SIZE

        # 排序字段映射
        sort_map = {
            "id": ProductArticle.id,
            "pre_publish_time": ProductArticle.pre_publish_time,
            "publish_time": ProductArticle.publish_time,
            "create_at": ProductArticle.create_at,
        }
        order_col = sort_map.get(sort, ProductArticle.create_at)
        order_exp = order_col.asc() if dir == "asc" else order_col.desc()

        articles = session.exec(base_query.order_by(order_exp).offset(offset_val).limit(PAGE_SIZE)).all()
        
        # 获取商品信息（当前页 + 过滤项）
        item_ids = [a.item_id for a in articles if a.item_id]
        if item_id and item_id not in item_ids:
            item_ids.append(item_id)

        product_map: dict[str, Product] = {}
        selected_product = None
        if item_ids:
            products = session.exec(select(Product).where(Product.item_id.in_(item_ids))).all()
            product_map = {p.item_id: p for p in products}
            if item_id:
                selected_product = product_map.get(item_id)
        
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

        # 统计已发布与待发布数量
        published_cnt = session.exec(
            select(func.count()).select_from(ProductArticle).where(ProductArticle.status == ArticleStatus.PUBLISHED)
        ).one()
        pending_cnt = session.exec(
            select(func.count()).select_from(ProductArticle).where(ProductArticle.status == ArticleStatus.PENDING_PUBLISH)
        ).one()

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
                "current_item_id": item_id or "",
                "selected_product": selected_product,
                "all_statuses": [s.value for s in ArticleStatus],
                "sort": sort or "",
                "dir": dir,
                "published_cnt": published_cnt,
                "pending_cnt": pending_cnt,
            },
        )


@router.get("/articles/{article_id}/edit", response_class=HTMLResponse)
async def edit_article_form(article_id: int, request: Request, current_user: dict = Depends(require_admin())):
    with Session(engine) as session:
        article = session.get(ProductArticle, article_id)
        if not article:
            raise HTTPException(status_code=404, detail="文章不存在")
        
        # 获取当前关联视频（如果有）
        mapping = session.exec(select(ArticleVideoMapping).where(ArticleVideoMapping.article_id == article_id)).first()
        current_video = None
        thumb_url = ""
        if mapping:
            video = session.get(Video, mapping.video_id)
            if video:
                current_video = video
                oss_service = OSSService()
                if oss_service.is_available():
                    style = "video/snapshot,t_1000,f_jpg,w_320,m_fast"
                    thumb_url = oss_service.bucket.sign_url("GET", video.oss_object_key, 3600, params={"x-oss-process": style})
        
        # 过滤掉 published 状态
        available_statuses = [s.value for s in ArticleStatus if s != ArticleStatus.PUBLISHED]
        
        return templates.TemplateResponse(
            "admin/article_form.html",
            {
                "request": request, 
                "user": current_user, 
                "article": article, 
                "statuses": available_statuses,
                "current_video": current_video,
                "thumb_url": thumb_url
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
        
        # 处理视频关联
        video_id_str = form_data.get("video_id", "").strip()
        mapping = session.exec(select(ArticleVideoMapping).where(ArticleVideoMapping.article_id == article_id)).first()

        if video_id_str:
            try:
                video_id = int(video_id_str)
            except ValueError:
                raise HTTPException(status_code=400, detail="无效的视频ID")

            video_obj = session.get(Video, video_id)
            if not video_obj:
                raise HTTPException(status_code=404, detail="视频不存在")

            if mapping:
                mapping.video_id = video_id
            else:
                mapping = ArticleVideoMapping(article_id=article_id, video_id=video_id)
                session.add(mapping)
        else:
            # 如果没传 video_id 且存在映射，删除映射
            if mapping:
                session.delete(mapping)

        session.commit()
        
    return RedirectResponse(url="/admin/articles", status_code=302)


# 批量删除文章
@router.post("/articles/batch-delete")
async def batch_delete_articles(ids: list[int], current_user: dict = Depends(require_admin())):
    if not ids:
        raise HTTPException(status_code=400, detail="ids 不能为空")
    with Session(engine) as session:
        # 先删除关联映射
        session.exec(sa.delete(ArticleVideoMapping).where(ArticleVideoMapping.article_id.in_(ids)))

        # 再删除文章
        articles = session.exec(select(ProductArticle).where(ProductArticle.id.in_(ids))).all()
        for art in articles:
            session.delete(art)
        session.commit()
    return {"status": "success", "count": len(articles)} 