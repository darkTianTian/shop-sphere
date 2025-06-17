import os
import tempfile
import logging
from typing import Dict, Any, Optional
import ffmpeg
from sqlmodel import Session
from app.internal.db import engine
from app.models.video import Video


class VideoService:
    """视频处理服务"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    def extract_video_metadata(self, video_path: str) -> Dict[str, Any]:
        """
        使用 ffmpeg 提取视频元数据
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            包含视频元数据的字典
        """
        try:
            # 使用 ffprobe 获取视频信息
            probe = ffmpeg.probe(video_path)
            
            # 获取视频流信息
            video_stream = None
            audio_stream = None
            
            for stream in probe['streams']:
                if stream['codec_type'] == 'video' and video_stream is None:
                    video_stream = stream
                elif stream['codec_type'] == 'audio' and audio_stream is None:
                    audio_stream = stream
            
            # 提取视频元数据
            metadata = {
                'format': probe['format'],
                'video': video_stream,
                'audio': audio_stream
            }
            
            return metadata
            
        except Exception as e:
            self.logger.error(f"提取视频元数据失败: {str(e)}")
            raise
    
    def convert_to_video_model(self, metadata: Dict[str, Any], item_id: str, sku_id: str, 
                              file_url: str, platform: str = "web", 
                              author_id: str = "", owner_id: str = "", 
                              source: str = "upload") -> Video:
        """
        将 ffmpeg 元数据转换为 Video 模型
        
        Args:
            metadata: ffmpeg 提取的元数据
            item_id: 商品ID
            sku_id: SKU ID
            file_url: 文件URL
            platform: 平台
            author_id: 作者ID
            owner_id: 所有者ID
            source: 来源
            
        Returns:
            Video 模型实例
        """
        format_info = metadata['format']
        video_info = metadata['video'] or {}
        audio_info = metadata['audio'] or {}
        
        # 提取基本信息
        duration_ms = int(float(format_info.get('duration', 0)) * 1000)
        file_id = os.path.basename(file_url)
        
        # 视频信息
        width = int(video_info.get('width', 0))
        height = int(video_info.get('height', 0))
        video_bitrate = int(video_info.get('bit_rate', 0))
        
        # 帧率处理
        frame_rate_str = video_info.get('r_frame_rate', '0/1')
        if '/' in frame_rate_str:
            num, den = frame_rate_str.split('/')
            frame_rate = int(float(num) / float(den)) if float(den) != 0 else 0
        else:
            frame_rate = int(float(frame_rate_str))
        
        # 音频信息
        audio_bitrate = int(audio_info.get('bit_rate', 0))
        audio_channels = int(audio_info.get('channels', 0))
        audio_sample_rate = int(audio_info.get('sample_rate', 0))
        
        # 色彩信息
        colour_primaries = video_info.get('color_primaries', 'unknown')
        matrix_coefficients = video_info.get('color_space', 'unknown')
        transfer_characteristics = video_info.get('color_transfer', 'unknown')
        
        # 旋转信息
        rotation = 0
        if 'tags' in video_info and 'rotate' in video_info['tags']:
            rotation = int(video_info['tags']['rotate'])
        
        # 创建 Video 实例
        video = Video(
            file_id=file_id,
            url=file_url,
            third_url="",
            item_id=item_id,
            sku_id=sku_id,
            width=width,
            height=height,
            duration=duration_ms,
            format=video_info.get('codec_name', 'unknown'),
            bitrate=video_bitrate,
            frame_rate=frame_rate,
            colour_primaries=colour_primaries,
            matrix_coefficients=matrix_coefficients,
            transfer_characteristics=transfer_characteristics,
            rotation=rotation,
            audio_bitrate=audio_bitrate,
            audio_channels=audio_channels,
            audio_duration=duration_ms,  # 通常音频和视频时长相同
            audio_format=audio_info.get('codec_name', 'unknown'),
            audio_sampling_rate=audio_sample_rate,
            cover_file_id="",  # 需要单独生成封面
            cover_url="",
            cover_width=width,
            cover_height=height,
            platform=platform,
            author_id=author_id,
            owner_id=owner_id,
            source=source
        )
        
        return video
    
    def save_video_to_db(self, video: Video) -> Video:
        """
        保存视频信息到数据库
        
        Args:
            video: Video 模型实例
            
        Returns:
            保存后的 Video 实例
        """
        try:
            with Session(engine) as session:
                session.add(video)
                session.commit()
                session.refresh(video)
                self.logger.info(f"视频信息已保存到数据库: {video.id}")
                return video
        except Exception as e:
            self.logger.error(f"保存视频信息到数据库失败: {str(e)}")
            raise
    
    def process_video_file(self, video_file_path: str, item_id: str, sku_id: str, 
                          file_url: str, **kwargs) -> Video:
        """
        处理视频文件：提取元数据并保存到数据库
        
        Args:
            video_file_path: 视频文件路径
            item_id: 商品ID
            sku_id: SKU ID
            file_url: 文件URL
            **kwargs: 其他参数
            
        Returns:
            保存后的 Video 实例
        """
        # 提取元数据
        metadata = self.extract_video_metadata(video_file_path)
        
        # 转换为 Video 模型
        video = self.convert_to_video_model(
            metadata=metadata,
            item_id=item_id,
            sku_id=sku_id,
            file_url=file_url,
            **kwargs
        )
        
        # 保存到数据库
        return self.save_video_to_db(video) 