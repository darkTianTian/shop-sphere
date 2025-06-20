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

router = APIRouter(prefix="/admin", tags=["videos"])

templates: Jinja2Templates = shared_templates

PAGE_SIZE = 30

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

        return templates.TemplateResponse(
            "admin/videos.html",
            {
                "request": request,
                "user": current_user,
                "videos": videos,
                "product_map": product_map,
                "VideoStatus": VideoStatus,
                "page": page,
                "total_pages": total_pages,
                "has_prev": page>1,
                "has_next": page<total_pages
            }
        ) 