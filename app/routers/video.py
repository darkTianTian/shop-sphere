import os
import tempfile
import logging
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.services.video_service import VideoService


# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/api/v1/videos", tags=["videos"])

# 视频服务实例
video_service = VideoService(logger=logger)


class VideoUploadResponse(BaseModel):
    """视频上传响应模型"""
    success: bool
    message: str
    video_id: Optional[int] = None
    video_info: Optional[dict] = None


@router.post("/upload", response_model=VideoUploadResponse)
async def upload_video(
    video_file: UploadFile = File(..., description="视频文件"),
    item_id: str = Form(..., description="商品ID"),
    sku_id: str = Form(None, description="SKU ID，如果不提供则使用item_id"),
    platform: str = Form("web", description="平台"),
    author_id: str = Form("", description="作者ID"),
    owner_id: str = Form("", description="所有者ID"),
    source: str = Form("upload", description="来源")
):
    """
    上传视频文件并提取元数据保存到数据库
    
    Args:
        video_file: 上传的视频文件
        item_id: 商品ID
        sku_id: SKU ID，可选，默认使用item_id
        platform: 平台，默认为web
        author_id: 作者ID，可选
        owner_id: 所有者ID，可选
        source: 来源，默认为upload
        
    Returns:
        VideoUploadResponse: 包含上传结果的响应
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
    
    temp_file_path = None
    try:
        # 创建临时文件保存上传的视频
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(video_file.filename)[1]) as temp_file:
            temp_file_path = temp_file.name
            
            # 读取并写入文件内容
            content = await video_file.read()
            temp_file.write(content)
            temp_file.flush()
        
        # 生成文件URL（这里简化处理，实际项目中可能需要上传到云存储）
        file_url = f"/uploads/videos/{video_file.filename}"
        
        # 处理视频文件
        video = video_service.process_video_file(
            video_file_path=temp_file_path,
            item_id=item_id,
            sku_id=sku_id,
            file_url=file_url,
            platform=platform,
            author_id=author_id,
            owner_id=owner_id,
            source=source
        )
        
        # 构建响应数据
        video_info = {
            "id": video.id,
            "file_id": video.file_id,
            "url": video.url,
            "item_id": video.item_id,
            "sku_id": video.sku_id,
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
            "source": video.source
        }
        
        logger.info(f"视频上传成功: {video_file.filename}, 数据库ID: {video.id}")
        
        return VideoUploadResponse(
            success=True,
            message="视频上传并处理成功",
            video_id=video.id,
            video_info=video_info
        )
        
    except Exception as e:
        logger.error(f"视频上传处理失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"视频处理失败: {str(e)}"
        )
    
    finally:
        # 清理临时文件
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as e:
                logger.warning(f"清理临时文件失败: {str(e)}")


@router.get("/{video_id}")
async def get_video(video_id: int):
    """
    根据ID获取视频信息
    
    Args:
        video_id: 视频ID
        
    Returns:
        视频信息
    """
    try:
        from sqlmodel import Session, select
        from app.internal.db import engine
        from app.models.video import Video
        
        with Session(engine) as session:
            video = session.get(Video, video_id)
            if not video:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="视频不存在"
                )
            
            return {
                "success": True,
                "data": {
                    "id": video.id,
                    "file_id": video.file_id,
                    "url": video.url,
                    "item_id": video.item_id,
                    "sku_id": video.sku_id,
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
                    "create_time": video.create_time,
                    "update_time": video.update_time
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


@router.get("/item/{item_id}")
async def get_videos_by_item(item_id: str):
    """
    根据商品ID获取视频列表
    
    Args:
        item_id: 商品ID
        
    Returns:
        视频列表
    """
    try:
        from sqlmodel import Session, select
        from app.internal.db import engine
        from app.models.video import Video
        
        with Session(engine) as session:
            videos = session.exec(
                select(Video).where(Video.item_id == item_id)
            ).all()
            
            video_list = []
            for video in videos:
                video_list.append({
                    "id": video.id,
                    "file_id": video.file_id,
                    "url": video.url,
                    "sku_id": video.sku_id,
                    "width": video.width,
                    "height": video.height,
                    "duration": video.duration,
                    "format": video.format,
                    "bitrate": video.bitrate,
                    "frame_rate": video.frame_rate,
                    "platform": video.platform,
                    "source": video.source,
                    "create_time": video.create_time
                })
            
            return {
                "success": True,
                "data": video_list,
                "count": len(video_list)
            }
            
    except Exception as e:
        logger.error(f"获取商品视频列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取商品视频列表失败: {str(e)}"
        ) 