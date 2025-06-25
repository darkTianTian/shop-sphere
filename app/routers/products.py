from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select, func
import math
from datetime import datetime
import json
from pydantic import BaseModel

from app.auth.decorators import require_admin
from app.internal.db import engine
from app.models.product import Product, ProductArticle, ArticleStatus, ProductStatus
from app.routers.admin import templates as shared_templates

router = APIRouter(prefix="/admin", tags=["products"])

templates: Jinja2Templates = shared_templates  # reuse filters

class ProductStatusUpdate(BaseModel):
    status: ProductStatus

@router.put("/products/{product_id}/status")
async def update_product_status(
    product_id: int,
    status_update: ProductStatusUpdate,
    current_user: dict = Depends(require_admin())
):
    """更新商品状态"""
    with Session(engine) as session:
        product = session.get(Product, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="商品不存在")
        
        product.status = status_update.status
        session.add(product)
        session.commit()
        return {"message": "状态更新成功"}

# ------------------ 商品 ------------------

@router.get("/products", response_class=HTMLResponse)
async def list_products(request: Request, current_user: dict = Depends(require_admin())):
    with Session(engine) as session:
        products = session.exec(select(Product).order_by(Product.item_create_time.desc())).all()
        return templates.TemplateResponse(
            "admin/products.html",
            {"request": request, "user": current_user, "products": products},
        )


@router.delete("/products/{product_id}")
async def delete_product(product_id: int, current_user: dict = Depends(require_admin())):
    with Session(engine) as session:
        product = session.get(Product, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="商品不存在")
        session.delete(product)
        session.commit()
        return {"ok": True}


# （文章相关路由已迁移至 app/routers/articles.py）

@router.get("/products/list")
async def list_products_api(current_user: dict = Depends(require_admin())):
    """返回商品列表的API"""
    with Session(engine) as session:
        products = session.exec(select(Product).order_by(Product.item_create_time.desc())).all()
        return [{
            "item_id": p.item_id,
            "item_name": p.item_name,
            "image_url": p.images[0].get('link') + '?imageView2/2/w/80/format/webp/q/75' if p.images else None,
            "first_sku_id": p.first_sku_id
        } for p in products]
