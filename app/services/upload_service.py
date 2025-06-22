import os
import tempfile
import logging
from typing import Tuple, Optional
from fastapi import UploadFile, HTTPException, status

from app.services.oss_service import OSSService
from app.services.video_service import VideoService


class UploadService:
    """通用文件上传服务"""
    
    def __init__(self, oss_service: OSSService, video_service: VideoService, logger: Optional[logging.Logger] = None):
        self.oss_service = oss_service
        self.video_service = video_service
        self.logger = logger or logging.getLogger(__name__)

    async def process_video_upload(
        self,
        video_file: UploadFile,
        item_id: str,
        sku_id: str = "",
        platform: str = "xiaohongshu",
        source: str = "upload",
        prefix: str = "video/material/",
        process_func: str = "process_video_material_file"
    ) -> Tuple[dict, str, str, int]:
        """
        处理视频文件上传的通用逻辑
        
        Args:
            video_file: 上传的视频文件
            item_id: 商品ID
            sku_id: SKU ID
            platform: 平台
            source: 来源
            prefix: OSS存储前缀
            process_func: 使用的处理函数名称（'process_video_material_file' 或 'process_video_file'）
            
        Returns:
            Tuple[dict, str, str, int]: (视频信息, 文件URL, OSS对象键, 文件大小)
        """
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
            self.logger.info(f"计算文件哈希: {video_file.filename}")
            file_hash = self.oss_service.calculate_file_hash(content)
            self.logger.info(f"文件哈希: {file_hash}")
            file_size = len(content)
            
            # 上传文件到OSS
            file_url = ""
            oss_object_key = ""
            
            #如果是测试环境，prefix前缀添加test
            self.logger.info(f"SERVER_ENVIRONMENT: {os.getenv('SERVER_ENVIRONMENT')}")
            if os.getenv("SERVER_ENVIRONMENT") == "LOCAL":
                prefix = "test/" + prefix

            if self.oss_service.is_available():
                # 上传到OSS
                success, result, public_url = self.oss_service.upload_temp_file(
                    temp_file_path, 
                    video_file.filename, 
                    video_file.content_type,
                    prefix=prefix,
                    file_hash=file_hash
                )
                
                if success:
                    oss_object_key = result
                    file_url = public_url
                    self.logger.info(f"文件上传到OSS成功: {video_file.filename} -> {oss_object_key}")
                else:
                    self.logger.error(f"OSS上传失败: {result}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail=f"文件上传失败: {result}"
                    )
            else:
                # 降级到本地存储
                file_url = f"/uploads/videos/{video_file.filename}"
                self.logger.error("OSS不可用，请检查配置")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="OSS不可用，请检查配置"
                )
            
            # 处理视频文件
            process_method = getattr(self.video_service, process_func)
            video = process_method(
                video_file_path=temp_file_path,
                item_id=item_id,
                sku_id=sku_id,
                file_url=file_url,
                file_extension=file_extension,
                oss_object_key=oss_object_key,
                file_size=file_size,
                platform=platform,
                source=source,
                file_hash=file_hash,
                name=video_file.filename
            )
            
            # 构建视频信息
            video_info = {
                "id": video.id,
                "file_extension": video.file_extension,
                "url": video.url,
                "file_hash": video.file_hash,
                "oss_object_key": video.oss_object_key,
                "file_size": video.file_size,
                "item_id": video.item_id,
                "sku_id": video.sku_id,
                "status": video.status if hasattr(video, 'status') else None,
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
                "is_oss_stored": bool(video.oss_object_key)
            }
            
            return video_info, file_url, oss_object_key, file_size
            
        finally:
            # 清理临时文件
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    self.logger.warning(f"清理临时文件失败: {str(e)}") 