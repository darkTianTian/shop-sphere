import os
import tempfile
import logging
import sys
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.services.video_service import VideoService
from app.services.oss_service import OSSService


# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout  # 将INFO日志输出到stdout
)
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/v1/video-materials", tags=["video-materials"])

# 视频素材服务实例
video_service = VideoService(logger=logger)
oss_service = OSSService(logger=logger)


class VideoMaterialUploadResponse(BaseModel):
    """视频素材上传响应模型"""
    success: bool
    message: str
    video_material_id: Optional[int] = None
    video_material_info: Optional[dict] = None


@router.post("/upload", response_model=VideoMaterialUploadResponse)
async def upload_video_material(
    video_file: UploadFile = File(..., description="视频文件"),
    item_id: str = Form(..., description="商品ID"),
    sku_id: str = Form(None, description="SKU ID，如果不提供则使用item_id"),
    description: str = Form(None, description="视频素材描述"),
    platform: str = Form("web", description="平台"),
    author_id: str = Form("", description="作者ID"),
    owner_id: str = Form("", description="所有者ID"),
    source: str = Form("upload", description="来源")
):
    """
    上传视频素材文件并提取元数据保存到数据库
    
    Args:
        video_file: 上传的视频文件
        item_id: 商品ID
        sku_id: SKU ID，可选，默认使用item_id
        platform: 平台，默认为web
        author_id: 作者ID，可选
        owner_id: 所有者ID，可选
        source: 来源，默认为upload
        
    Returns:
        VideoMaterialUploadResponse: 包含上传结果的响应
    """
    
    # 验证文件类型
    if not video_file.content_type or not video_file.content_type.startswith('video/'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="上传的文件必须是视频格式"
        )
    
    # 如果没有提供sku_id，使用item_id
    if not sku_id:
        sku_id = item_id
    
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
        
        # 上传文件到OSS
        file_url = ""
        oss_object_key = ""
        file_size = len(content)
        
        if oss_service.is_available():
            # 上传到OSS
            success, result, public_url = oss_service.upload_temp_file(
                temp_file_path, 
                video_file.filename, 
                video_file.content_type
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
            logger.warning("OSS不可用，使用本地存储")
        
        # 处理视频文件
        video_material = video_service.process_video_file(
            video_file_path=temp_file_path,
            item_id=item_id,
            sku_id=sku_id,
            file_url=file_url,
            name=video_file.filename,
            description=description,
            file_extension=file_extension,
            oss_object_key=oss_object_key,
            file_size=file_size,
            platform=platform,
            author_id=author_id,
            owner_id=owner_id,
            source=source
        )
        
        # 构建响应数据
        video_material_info = {
            "id": video_material.id,
            "name": video_material.name,
            "description": video_material.description,
            "file_extension": video_material.file_extension,
            "uuid": video_material.uuid,
            "url": video_material.url,
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
            "is_oss_stored": bool(video_material.oss_object_key)  # 标识是否存储在OSS
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


@router.get("/{video_material_id}")
async def get_video_material(video_material_id: int):
    """
    根据ID获取视频素材信息
    
    Args:
        video_material_id: 视频素材ID
        
    Returns:
        视频素材信息
    """
    try:
        from sqlmodel import Session, select
        from app.internal.db import engine
        from app.models.video import VideoMaterial
        
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


@router.get("/item/{item_id}")
async def get_video_materials_by_item(item_id: str):
    """
    根据商品ID获取视频素材列表
    
    Args:
        item_id: 商品ID
        
    Returns:
        视频素材列表
    """
    try:
        from sqlmodel import Session, select
        from app.internal.db import engine
        from app.models.video import VideoMaterial
        
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