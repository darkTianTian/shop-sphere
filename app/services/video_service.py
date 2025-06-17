import os
import tempfile
import logging
from typing import Dict, Any, Optional
import ffmpeg
from sqlmodel import Session
from app.internal.db import engine
from app.models.video import VideoMaterial


class VideoService:
    """视频素材处理服务"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
    
    def _map_video_format(self, codec_name: str) -> str:
        """
        将 FFmpeg 的编码器名称映射为标准格式名称
        
        Args:
            codec_name: FFmpeg 返回的编码器名称
            
        Returns:
            标准格式名称
        """
        format_mapping = {
            'h264': 'AVC',
            'h265': 'HEVC',
            'hevc': 'HEVC',
            'vp8': 'VP8',
            'vp9': 'VP9',
            'av1': 'AV1',
            'mpeg4': 'MPEG4',
            'mpeg2video': 'MPEG2',
            'wmv3': 'WMV',
            'flv1': 'FLV',
            'theora': 'Theora'
        }
        return format_mapping.get(codec_name.lower(), codec_name.upper())
    
    def _map_audio_format(self, codec_name: str) -> str:
        """
        将 FFmpeg 的音频编码器名称映射为标准格式名称
        
        Args:
            codec_name: FFmpeg 返回的音频编码器名称
            
        Returns:
            标准格式名称
        """
        format_mapping = {
            'aac': 'AAC',
            'mp3': 'MP3',
            'opus': 'OPUS',
            'vorbis': 'Vorbis',
            'flac': 'FLAC',
            'pcm_s16le': 'PCM',
            'ac3': 'AC3',
            'eac3': 'EAC3'
        }
        return format_mapping.get(codec_name.lower(), codec_name.upper())
    
    def _map_color_info(self, color_value: str) -> str:
        """
        将 FFmpeg 的色彩信息映射为标准格式
        
        Args:
            color_value: FFmpeg 返回的色彩信息值
            
        Returns:
            标准色彩信息格式
        """
        if not color_value or color_value.lower() in ['unknown', 'unspecified', '']:
            return 'BT.709'
        
        color_mapping = {
            'bt709': 'BT.709',
            'bt.709': 'BT.709',
            'rec709': 'BT.709',
            'bt2020': 'BT.2020',
            'bt.2020': 'BT.2020',
            'rec2020': 'BT.2020',
            'bt601': 'BT.601',
            'bt.601': 'BT.601',
            'rec601': 'BT.601',
            'smpte170m': 'BT.601',
            'smpte240m': 'SMPTE-240M',
            'srgb': 'sRGB',
            'displayp3': 'Display P3'
        }
        
        return color_mapping.get(color_value.lower(), 'BT.709')
    
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
                              file_url: str, name: str, description: str = "", 
                              file_extension: str = "", platform: str = "web", 
                              author_id: str = "", owner_id: str = "", 
                              source: str = "upload") -> VideoMaterial:
        """
        将 ffmpeg 元数据转换为 VideoMaterial 模型
        
        Args:
            metadata: ffmpeg 提取的元数据
            item_id: 商品ID
            sku_id: SKU ID
            file_url: 文件URL
            name: 视频素材名称
            description: 视频素材描述
            file_extension: 文件扩展名
            platform: 平台
            author_id: 作者ID
            owner_id: 所有者ID
            source: 来源
            
        Returns:
            VideoMaterial 模型实例
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
        
        # 色彩信息映射
        colour_primaries = self._map_color_info(video_info.get('color_primaries', ''))
        matrix_coefficients = self._map_color_info(video_info.get('color_space', ''))
        transfer_characteristics = self._map_color_info(video_info.get('color_transfer', ''))
        
        # 旋转信息
        rotation = 0
        if 'tags' in video_info and 'rotate' in video_info['tags']:
            rotation = int(video_info['tags']['rotate'])
        
        # 格式映射
        video_format = self._map_video_format(video_info.get('codec_name', 'unknown'))
        audio_format = self._map_audio_format(audio_info.get('codec_name', 'unknown'))
        
        # 创建 VideoMaterial 实例
        video_material = VideoMaterial(
            name=name,
            description=description,
            file_extension=file_extension,
            url=file_url,
            item_id=item_id,
            sku_id=sku_id,
            width=width,
            height=height,
            duration=duration_ms,
            format=video_format,
            bitrate=video_bitrate,
            frame_rate=frame_rate,
            colour_primaries=colour_primaries,
            matrix_coefficients=matrix_coefficients,
            transfer_characteristics=transfer_characteristics,
            rotation=rotation,
            audio_bitrate=audio_bitrate,
            audio_channels=audio_channels,
            audio_duration=duration_ms,  # 通常音频和视频时长相同
            audio_format=audio_format,
            audio_sampling_rate=audio_sample_rate,
            cover_url="",
            cover_width=width,
            cover_height=height,
            platform=platform,
            author_id=author_id,
            owner_id=owner_id,
            source=source
        )
        
        return video_material
    
    def save_video_to_db(self, video_material: VideoMaterial) -> VideoMaterial:
        """
        保存视频素材信息到数据库
        
        Args:
            video_material: VideoMaterial 模型实例
            
        Returns:
            保存后的 VideoMaterial 实例
        """
        try:
            with Session(engine) as session:
                session.add(video_material)
                session.commit()
                session.refresh(video_material)
                self.logger.info(f"视频素材信息已保存到数据库: {video_material.id}")
                return video_material
        except Exception as e:
            self.logger.error(f"保存视频素材信息到数据库失败: {str(e)}")
            raise
    
    def process_video_file(self, video_file_path: str, item_id: str, sku_id: str, 
                          file_url: str, **kwargs) -> VideoMaterial:
        """
        处理视频文件：提取元数据并保存到数据库
        
        Args:
            video_file_path: 视频文件路径
            item_id: 商品ID
            sku_id: SKU ID
            file_url: 文件URL
            **kwargs: 其他参数
            
        Returns:
            保存后的 VideoMaterial 实例
        """
        # 提取元数据
        metadata = self.extract_video_metadata(video_file_path)
        
        # 转换为 VideoMaterial 模型
        video_material = self.convert_to_video_model(
            metadata=metadata,
            item_id=item_id,
            sku_id=sku_id,
            file_url=file_url,
            **kwargs
        )
        
        # 保存到数据库
        return self.save_video_to_db(video_material) 