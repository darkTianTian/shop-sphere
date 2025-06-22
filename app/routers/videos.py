import os
import tempfile
import logging
import sys
import math
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status, Depends, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from sqlmodel import Session, select, func

from app.services.video_service import VideoService
from app.services.oss_service import OSSService
from app.services.upload_service import UploadService
from app.auth.decorators import require_admin
from app.internal.db import engine
from app.models.video import VideoMaterial, VideoStatus, Video
from app.routers.admin import templates as shared_templates
from app.models.product import Product

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/admin/videos", tags=["videos"])

# 服务实例
video_service = VideoService(logger=logger)
oss_service = OSSService(logger=logger)
upload_service = UploadService(oss_service=oss_service, video_service=video_service, logger=logger)

templates: Jinja2Templates = shared_templates

PAGE_SIZE = 30

class VideoMaterialUploadResponse(BaseModel):
    """视频素材上传响应模型"""
    success: bool
    message: str
    video_material_id: Optional[int] = None
    video_material_info: Optional[dict] = None

class VideoStatusUpdate(BaseModel):
    """视频状态更新模型"""
    is_enabled: bool  # 期望接收 is_enabled 字段

class VideoMaterialStatusUpdate(BaseModel):
    """视频素材状态更新模型"""
    status: str

# ------------------ 视频管理页面 ------------------

@router.get("", response_class=HTMLResponse)
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

@router.get("/{video_id}/play")
async def play_video(video_id: int, current_user: dict = Depends(require_admin())):
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
        return {"url": signed_url}

# ------------------ 视频上传和管理API ------------------

async def check_video_file(video_file: UploadFile) -> None:
    """
    检查视频文件的类型和大小
    
    Args:
        video_file: 上传的视频文件
        
    Raises:
        HTTPException: 当文件类型不正确或大小超限时抛出
    """
    # 验证文件类型
    if not video_file.content_type or not video_file.content_type.startswith('video/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="上传的文件必须是视频格式"
        )

    # 检查文件大小
    MAX_FILE_SIZE = 200 * 1024 * 1024  # 500MB in bytes
    try:
        size = 0
        while chunk := await video_file.read(8192):  # 8KB chunks
            size += len(chunk)
            if size > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"文件大小超过限制（最大500MB）"
                )
        # 重置文件指针
        await video_file.seek(0)
    except Exception as e:
        if not isinstance(e, HTTPException):
            logger.error(f"检查文件大小时出错: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="检查文件大小时出错"
            )
        raise e

@router.post("/upload", response_model=VideoMaterialUploadResponse)
async def upload_video_material(
    video_file: UploadFile = File(..., description="视频文件"),
    item_id: str = Form(..., description="商品ID"),
    sku_id: str = Form(None, description="SKU ID，如果不提供则使用item_id"),
    platform: str = Form("xiaohongshu", description="平台"),
    source: str = Form("upload", description="来源"),
    current_user: dict = Depends(require_admin())
):
    """上传视频素材文件并提取元数据保存到数据库"""
    try:
        # 使用通用上传服务处理视频上传
        video_info, file_url, oss_object_key, file_size = await upload_service.process_video_upload(
            video_file=video_file,
            item_id=item_id,
            sku_id=sku_id or "",
            platform=platform,
            source=source,
            prefix="video/material/",
            process_func="process_video_material_file"
        )
        
        logger.info(f"视频素材上传成功: {video_file.filename}, 数据库ID: {video_info['id']}")
        
        return VideoMaterialUploadResponse(
            success=True,
            message="视频素材上传并处理成功",
            video_material_id=video_info['id'],
            video_material_info=video_info
        )
        
    except Exception as e:
        logger.error(f"视频素材上传处理失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"视频素材处理失败: {str(e)}"
        )

@router.get("/api/v1/videos/{video_identifier}")
async def get_video(
    video_identifier: str, 
    current_user: dict = Depends(require_admin())
):
    """根据ID或ULID获取视频信息"""
    try:
        with Session(engine) as session:
            # 尝试作为ULID查询
            video = session.exec(
                select(VideoMaterial).where(VideoMaterial.ulid == video_identifier)
            ).first()
            
            # 如果找不到，尝试作为ID查询
            if not video and video_identifier.isdigit():
                video = session.get(VideoMaterial, int(video_identifier))
            
            if not video:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="视频不存在"
                )
            
            return {
                "success": True,
                "data": {
                    "id": video.id,
                    "ulid": video.ulid,
                    "name": video.name,
                    "description": video.description,
                    "file_extension": video.file_extension,
                    "url": video.url,
                    "item_id": video.item_id,
                    "sku_id": video.sku_id,
                    "status": video.status,
                    "width": video.width,
                    "height": video.height,
                    "duration": video.duration,
                    "format": video.format,
                    "bitrate": video.bitrate,
                    "frame_rate": video.frame_rate,
                    "audio_format": video.audio_format,
                    "audio_bitrate": video.audio_bitrate,
                    "audio_channels": video.audio_channels,
                    "platform": video.platform,
                    "source": video.source,
                    "create_time": video.create_at,
                    "update_time": video.update_at
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取视频信息失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取视频信息失败: {str(e)}"
        )

@router.get("/api/v1/video-materials/item/{item_id}")
async def get_video_materials_by_item(item_id: str, current_user: dict = Depends(require_admin())):
    """根据商品ID获取视频素材列表"""
    try:
        with Session(engine) as session:
            video_materials = session.exec(
                select(VideoMaterial).where(VideoMaterial.item_id == item_id)
            ).all()
            
            video_material_list = []
            for video_material in video_materials:
                video_material_list.append({
                    "id": video_material.id,
                    "name": video_material.name,
                    "description": video_material.description,
                    "file_extension": video_material.file_extension,
                    "uuid": video_material.uuid,
                    "url": video_material.url,
                    "sku_id": video_material.sku_id,
                    "status": video_material.status,
                    "width": video_material.width,
                    "height": video_material.height,
                    "duration": video_material.duration,
                    "format": video_material.format,
                    "bitrate": video_material.bitrate,
                    "frame_rate": video_material.frame_rate,
                    "audio_format": video_material.audio_format,
                    "audio_bitrate": video_material.audio_bitrate,
                    "audio_channels": video_material.audio_channels,
                    "platform": video_material.platform,
                    "source": video_material.source,
                    "create_time": video_material.create_time,
                    "update_time": video_material.update_time
                })
            
            return {
                "success": True,
                "data": video_material_list,
                "count": len(video_material_list)
            }
            
    except Exception as e:
        logger.error(f"获取商品视频素材列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取商品视频素材列表失败: {str(e)}"
        )

@router.put("/{video_id}/status", response_model=dict)
async def update_video_material_status(
    video_id: int, 
    status_update: VideoMaterialStatusUpdate,
    current_user: dict = Depends(require_admin())
):
    """更新视频素材状态"""
    try:
        with Session(engine) as session:
            video = session.get(VideoMaterial, video_id)
            if not video:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="视频不存在"
                )
            
            # 验证状态值是否有效
            try:
                new_status = VideoStatus(status_update.status)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="无效的状态值"
                )
            
            # 更新状态
            video.status = new_status
            session.add(video)
            session.commit()
            session.refresh(video)
            
            return {"success": True, "message": "状态更新成功"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新视频状态失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新视频状态失败: {str(e)}"
        )

@router.get("/published", response_class=HTMLResponse)
async def list_published_videos(request: Request, page: int = 1, current_user: dict = Depends(require_admin())):
    """已发布视频列表页面"""
    page = max(page, 1)
    with Session(engine) as session:
        total = session.exec(select(func.count(Video.id))).one()
        total_pages = max(math.ceil(total/PAGE_SIZE), 1)
        offset_val = (page - 1) * PAGE_SIZE
        videos = session.exec(
            select(Video).order_by(Video.create_at.desc()).offset(offset_val).limit(PAGE_SIZE)
        ).all()

        # 取商品信息
        item_ids = [v.item_id for v in videos if v.item_id]
        product_map = {}
        if item_ids:
            products = session.exec(select(Product).where(Product.item_id.in_(item_ids))).all()
            product_map = {p.item_id: p for p in products}

        # 缩略图
        thumb_map = {}
        if oss_service.is_available():
            for v in videos:
                style = "video/snapshot,t_1000,f_jpg,w_320,m_fast"
                thumb_map[v.id] = oss_service.bucket.sign_url("GET", v.oss_object_key, 3600, params={"x-oss-process": style})

        return templates.TemplateResponse(
            "admin/published_videos.html",
            {
                "request": request,
                "user": current_user,
                "videos": videos,
                "product_map": product_map,
                "thumb_map": thumb_map,
                "page": page,
                "total_pages": total_pages,
                "has_prev": page > 1,
                "has_next": page < total_pages,
            },
        )

@router.post("/publish/upload", response_model=dict)
async def upload_published_video(
    video_file: UploadFile = File(..., description="视频文件"),
    item_id: str = Form(..., description="商品ID"),
    platform: str = Form("xiaohongshu", description="平台"),
    current_user: dict = Depends(require_admin())
):
    """上传视频并存到 Video 表（待发布）"""
    try:
        # 使用通用上传服务处理视频上传
        video_info, _, _, _ = await upload_service.process_video_upload(
            video_file=video_file,
            item_id=item_id,
            platform=platform,
            prefix="video/publish/",
            process_func="process_video_file"
        )
        
        return {"success": True, "message": "视频上传成功", "video_id": video_info['id']}
        
    except Exception as e:
        logger.error(f"视频上传失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"视频上传失败: {str(e)}"
        )

@router.put("/published/{video_id}/status", response_model=dict)
async def update_published_video_status(
    video_id: int, 
    status_update: VideoStatusUpdate,
    current_user: dict = Depends(require_admin())
):
    """更新待发布视频状态"""
    try:
        with Session(engine) as session:
            video = session.get(Video, video_id)
            if not video:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="视频不存在"
                )
            
            # 更新状态
            video.is_enabled = status_update.is_enabled
            session.add(video)
            session.commit()
            session.refresh(video)
            
            return {"success": True, "message": "状态更新成功"}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新视频状态失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新视频状态失败: {str(e)}"
        )

@router.get("/published/{video_id}/play")
async def play_published_video(video_id: int, current_user: dict = Depends(require_admin())):
    """
    返回待发布视频的可直接播放的临时 URL（有效 1 小时）
    """
    with Session(engine) as s:
        v = s.get(Video, video_id)
        if not v:
            raise HTTPException(404, "视频不存在")
        if not oss_service.is_available():
            raise HTTPException(500, "OSS 未配置")

        # 使用 oss_object_key 而不是 file_id
        signed_url = oss_service.bucket.sign_url(
            'GET', v.oss_object_key, expires=3600
        )
        return {"url": signed_url}