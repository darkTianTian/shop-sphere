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

# 视频素材服务实例
video_service = VideoService(logger=logger)
oss_service = OSSService(logger=logger)

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
    is_enabled: bool

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
    
    # 检查视频文件
    await check_video_file(video_file)

    # 获取文件扩展名
    file_extension = os.path.splitext(video_file.filename)[1].lower()
    
    temp_file_path = None
    try:
        # 创建临时文件保存上传的视频
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            temp_file_path = temp_file.name
            # 读取并写入文件内容
            content = await video_file.read()
            temp_file.write(content)
            temp_file.flush()
        
        # 计算文件哈希
        file_hash = oss_service.calculate_file_hash(content)
        file_size = len(content)
        
        # 上传文件到OSS
        file_url = ""
        oss_object_key = ""
        
        if oss_service.is_available():
            # 上传到OSS
            success, result, public_url = oss_service.upload_temp_file(
                temp_file_path, 
                video_file.filename, 
                video_file.content_type,
                prefix="video/material/",
                file_hash=file_hash
            )
            
            if success:
                oss_object_key = result
                file_url = public_url
                logger.info(f"文件上传到OSS成功: {video_file.filename} -> {oss_object_key}")
            else:
                logger.error(f"OSS上传失败: {result}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"文件上传失败: {result}"
                )
        else:
            # 降级到本地存储
            file_url = f"/uploads/videos/{video_file.filename}"
            logger.error("OSS不可用，请检查配置")
        
        # 处理视频文件
        video_material = video_service.process_video_material_file(
            video_file_path=temp_file_path,
            item_id=item_id,
            sku_id="",
            file_url=file_url,
            file_extension=file_extension,
            oss_object_key=oss_object_key,
            file_size=file_size,
            platform=platform,
            source=source,
            file_hash=file_hash
        )
        
        # 构建响应数据
        video_material_info = {
            "id": video_material.id,
            "file_extension": video_material.file_extension,
            "url": video_material.url,
            "file_hash": video_material.file_hash,
            "oss_object_key": video_material.oss_object_key,
            "file_size": video_material.file_size,
            "item_id": video_material.item_id,
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
            "is_oss_stored": bool(video_material.oss_object_key)
        }
        
        logger.info(f"视频素材上传成功: {video_file.filename}, 数据库ID: {video_material.id}")
        
        return VideoMaterialUploadResponse(
            success=True,
            message="视频素材上传并处理成功",
            video_material_id=video_material.id,
            video_material_info=video_material_info
        )
        
    except Exception as e:
        logger.error(f"视频素材上传处理失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"视频素材处理失败: {str(e)}"
        )
    
    finally:
        # 清理临时文件
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                logger.warning(f"清理临时文件失败: {str(e)}")
                

@router.get("/api/v1/video-materials/{video_material_id}")
async def get_video_material(video_material_id: int, current_user: dict = Depends(require_admin())):
    """根据ID获取视频素材信息"""
    try:
        with Session(engine) as session:
            video_material = session.get(VideoMaterial, video_material_id)
            if not video_material:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="视频素材不存在"
                )
            
            return {
                "success": True,
                "data": {
                    "id": video_material.id,
                    "name": video_material.name,
                    "description": video_material.description,
                    "file_extension": video_material.file_extension,
                    "uuid": video_material.uuid,
                    "url": video_material.url,
                    "item_id": video_material.item_id,
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
                }
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取视频素材信息失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取视频素材信息失败: {str(e)}"
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
async def update_video_status(
    video_id: int, 
    status_update: VideoStatusUpdate,
    current_user: dict = Depends(require_admin())
):
    """更新视频状态"""
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

    # 检查视频文件
    await check_video_file(video_file)
    file_extension = os.path.splitext(video_file.filename)[1].lower()

    temp_file_path = None
    try:
        # 保存到临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
            temp_file_path = temp_file.name
            content = await video_file.read()
            temp_file.write(content)
            temp_file.flush()

        file_hash = oss_service.calculate_file_hash(content)
        file_size = len(content)

        # 上传到 OSS
        file_url = ""
        oss_object_key = ""
        if oss_service.is_available():
            success, result, public_url = oss_service.upload_temp_file(
                temp_file_path, 
                video_file.filename,
                video_file.content_type,
                prefix="video/publish/",
                file_hash=file_hash
            )
            
            if success:
                oss_object_key = result
                file_url = public_url
                logger.info(f"文件上传到OSS成功: {video_file.filename} -> {oss_object_key}")
            else:
                logger.error(f"OSS上传失败: {result}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"文件上传失败: {result}"
                )
        else:
            logger.error("OSS不可用，请检查配置")

        video = video_service.process_video_file(
            video_file_path=temp_file_path,
            item_id=item_id,
            sku_id="",
            file_url=file_url,
            file_extension=file_extension,
            oss_object_key=oss_object_key,
            file_size=file_size,
            platform=platform,
            file_hash=file_hash
        )

        return {"success": True, "message": "视频上传成功", "video_id": video.id}
    except Exception as e:
        logger.error(f"视频上传失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"视频上传失败: {str(e)}"
        )
    
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                logger.warning(f"清理临时文件失败: {str(e)}")

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