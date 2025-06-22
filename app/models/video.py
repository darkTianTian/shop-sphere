from datetime import datetime
import uuid
import sqlalchemy as sa
from enum import Enum
from sqlmodel import SQLModel, Field
from app.models.base import BaseModel
from typing import Optional


class VideoStatus(str, Enum):
    """视频状态"""
    DRAFT = "draft"
    DELETED = "deleted"


class VideoMataData(SQLModel, table=False):
    """视频素材元数据"""
    width: int = Field(description="视频宽度")
    height: int = Field(description="视频高度")
    duration: int = Field(description="视频时长毫秒")
    format: str = Field(description="视频格式")
    bitrate: int = Field(description="视频比特率")
    frame_rate: int = Field(description="视频帧率")
    colour_primaries: str = Field(description="视频色彩空间")
    matrix_coefficients: str = Field(description="视频矩阵系数")
    transfer_characteristics: str = Field(description="视频传输特性")
    rotation: int = Field(description="视频旋转角度")
    audio_bitrate: int = Field(description="音频比特率")
    audio_channels: int = Field(description="音频通道数")
    audio_duration: int = Field(description="音频时长毫秒")
    audio_format: str = Field(description="音频格式")
    audio_sampling_rate: int = Field(description="音频采样率")


class VideoCommonData(SQLModel, table=False):
    """视频公共数据"""
    name: str = Field(default="", description="视频名称", sa_type=sa.String(length=128))
    file_hash: str = Field(default="", index=True, description="文件SHA256哈希值", sa_type=sa.String(length=64))
    file_extension: str = Field(description="文件扩展名", sa_type=sa.String(length=10))
    file_size: int = Field(default=0, description="文件大小（字节）")
    item_id: str = Field(index=True, description="商品ID")
    sku_id: str = Field(index=True, description="SKU ID")
    platform: str = Field(description="平台", sa_type=sa.String(length=32))
    owner_id: str = Field(index=True, description="所有者ID")
    source: str = Field(description="来源", sa_type=sa.String(length=32), default="upload")
    oss_object_key: str = Field(default="", description="OSS对象键名", sa_type=sa.String(length=512))
    url: str = Field(index=True, description="视频URL")


class VideoMaterial(VideoMataData, VideoCommonData, BaseModel, table=True):
    """
    视频素材模型 - 存储原始视频文件的元数据信息
    
    "fileid": "spectrum/wqUwPjW8yPnnPN4jaxy92x9WGKLRqvhX2HVsNu2nv2y8Icw",
            "file_id": "spectrum/wqUwPjW8yPnnPN4jaxy92x9WGKLRqvhX2HVsNu2nv2y8Icw",
            "format_width": 1080,
            "format_height": 1920,
            "video_preview_type": "full_vertical_screen",
            "composite_metadata": {
                "video": {
                    "bitrate": 11455306,
                    "colour_primaries": "BT.709",
                    "duration": 22867,
                    "format": "AVC",
                    "frame_rate": 30,
                    "height": 1920,
                    "matrix_coefficients": "BT.709",
                    "rotation": 0,
                    "transfer_characteristics": "BT.709",
                    "width": 1080
                },
                "audio": {
                    "bitrate": 93918,
                    "channels": 2,
                    "duration": 22848,
                    "format": "AAC",
                    "sampling_rate": 44100
                }
            },
            "timelines": [],
            "cover": {
                "fileid": "110/0/01e75947f42c0c3000100000000193b4c12534_0.jpg",
                "file_id": "110/0/01e75947f42c0c3000100000000193b4c12534_0.jpg",
                "height": 1920,
                "width": 1080,
                "frame": {
                    "ts": 0,                    # 时间戳：第0秒作为封面
                    "is_user_select": False,    # 是否用户选择：系统自动选择
                    "is_upload": False          # 是否上传的封面：系统生成
                }
            },"""
    __tablename__ = "video_material"
    status: str = Field(description="状态", sa_type=sa.Enum(VideoStatus), default=VideoStatus.DRAFT)
    author_id: str = Field(default="", description="原平台作者ID")


class Video(VideoMataData, VideoCommonData, BaseModel, table=True):
    """待发布视频"""
    third_file_id: str = Field(nullable=True, index=True, description="三方平台文件ID")
    cover_file_id: str = Field(nullable=True, description="封面文件ID")
    video_material_id: str = Field(nullable=True, index=True, description="VideoMaterial.ID")
    is_enabled: bool = Field(default=True, description="是否可用")
    publish_cnt: int = Field(default=0, description="发布次数")

