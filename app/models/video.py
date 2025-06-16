from datetime import datetime
import sqlalchemy as sa
from sqlmodel import SQLModel, Field
from app.models.base import BaseModel

class Video(BaseModel, table=True):
    """
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
    file_id: str = Field(index=True, description="文件ID")
    url: str = Field(index=True, description="视频URL")
    third_url: str = Field(description="第三方视频URL")
    item_id: str = Field(index=True, description="商品ID")
    sku_id: str = Field(index=True, description="SKU ID")
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
    cover_file_id: str = Field(description="封面文件ID")
    cover_url: str = Field(description="封面URL")
    cover_width: int = Field(description="封面宽度")
    cover_height: int = Field(description="封面高度")
    platform: str = Field(description="平台", sa_type=sa.String(length=32))
    author_id: str = Field(description="作者ID")
    owner_id: str = Field(index=True, description="所有者ID")
    source: str = Field(description="来源", sa_type=sa.String(length=32))
