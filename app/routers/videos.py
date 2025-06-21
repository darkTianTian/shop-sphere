from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select, func
import math

from app.auth.decorators import require_admin
from app.internal.db import engine
from app.models.video import VideoMaterial, VideoStatus
from app.routers.admin import templates as shared_templates
from app.models.product import Product
from app.services.oss_service import OSSService

router = APIRouter(prefix="/admin", tags=["videos"])

templates: Jinja2Templates = shared_templates

PAGE_SIZE = 30

oss_service = OSSService()

@router.get("/videos", response_class=HTMLResponse)
async def list_videos(request: Request, page: int = 1, current_user: dict = Depends(require_admin())):
    page = max(page, 1)
    with Session(engine) as session:
        total = session.exec(select(func.count(VideoMaterial.id))).one()
        total_pages = max(math.ceil(total/PAGE_SIZE),1)
        offset_val = (page-1)*PAGE_SIZE
        videos = session.exec(select(VideoMaterial).order_by(VideoMaterial.create_at.desc()).offset(offset_val).limit(PAGE_SIZE)).all()

        item_ids = [v.item_id for v in videos if v.item_id]
        product_map: dict[str, Product] = {}
        if item_ids:
            products = session.exec(select(Product).where(Product.item_id.in_(item_ids))).all()
            product_map = {p.item_id: p for p in products}

        # 生成缩略图签名URL
        thumb_map: dict[int,str] = {}
        if oss_service.is_available():
            for v in videos:
                style = "video/snapshot,t_1000,f_jpg,w_320,m_fast"
                thumb_map[v.id] = oss_service.bucket.sign_url('GET', v.oss_object_key, 3600, params={'x-oss-process': style})

        return templates.TemplateResponse(
            "admin/videos.html",
            {
                "request": request,
                "user": current_user,
                "videos": videos,
                "product_map": product_map,
                "VideoStatus": VideoStatus,
                "thumb_map": thumb_map,
                "page": page,
                "total_pages": total_pages,
                "has_prev": page>1,
                "has_next": page<total_pages
            }
        )

@router.get("/videos/{video_id}/play")
async def play_video(video_id: int, current_user=Depends(require_admin())):
    """
    返回可以直接播放的临时 URL（有效 1 小时）
    """
    with Session(engine) as s:
        v = s.get(VideoMaterial, video_id)
        if not v:
            raise HTTPException(404, "视频不存在")
        if not oss_service.is_available():
            raise HTTPException(500, "OSS 未配置")

        # object_key 就是表里保存的 oss_object_key
        signed_url = oss_service.bucket.sign_url(
            'GET', v.oss_object_key, expires=3600
        )
        #TODO: 这里需要做redis缓存
        return {"url": signed_url}