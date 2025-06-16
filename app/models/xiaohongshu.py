from typing import List, Optional, Dict, Any
from dataclasses import dataclass, asdict
import json
from app.models.video import Video

@dataclass
class HashTag:
    """话题标签数据模型"""
    id: str
    name: str
    link: str
    type: str = "topic"


@dataclass
class VideoMetadata:
    """视频元数据"""
    bitrate: int
    colour_primaries: str
    duration: int
    format: str
    frame_rate: int
    height: int
    matrix_coefficients: str
    rotation: int
    transfer_characteristics: str
    width: int


@dataclass
class AudioMetadata:
    """音频元数据"""
    bitrate: int
    channels: int
    duration: int
    format: str
    sampling_rate: int


@dataclass
class CompositeMetadata:
    """复合媒体元数据"""
    video: VideoMetadata
    audio: AudioMetadata


@dataclass
class CoverFrame:
    """封面帧信息"""
    ts: int
    is_user_select: bool
    is_upload: bool


@dataclass
class Cover:
    """封面信息"""
    fileid: str
    file_id: str
    height: int
    width: int
    frame: CoverFrame


@dataclass
class SegmentItem:
    """视频片段项"""
    mute: int
    speed: int
    start: int
    duration: float
    transcoded: int
    media_source: int
    original_metadata: CompositeMetadata


@dataclass
class Segments:
    """视频片段信息"""
    count: int
    need_slice: bool
    items: List[SegmentItem]


@dataclass
class VideoInfo:
    """视频信息"""
    fileid: str
    file_id: str
    format_width: int
    format_height: int
    video_preview_type: str
    composite_metadata: CompositeMetadata
    timelines: List[Any]
    cover: Cover
    chapters: List[Any]
    chapter_sync_text: bool
    segments: Segments
    entrance: str


@dataclass
class PrivacyInfo:
    """隐私信息"""
    op_type: int
    type: int


@dataclass
class GoodsExtension:
    """商品扩展信息"""
    live_preheat: str


@dataclass
class GoodsInfo:
    """商品信息"""
    extension: GoodsExtension


@dataclass
class BizRelation:
    """业务关系"""
    biz_type: str
    biz_id: str
    extra_info: str


@dataclass
class CommonInfo:
    """笔记通用信息"""
    type: str
    note_id: str
    source: str
    title: str
    desc: str
    ats: List[Any]
    hash_tag: List[HashTag]
    business_binds: str
    privacy_info: PrivacyInfo
    goods_info: GoodsInfo
    biz_relations: List[BizRelation]


@dataclass
class XiaohongshuNote:
    """小红书笔记完整数据模型"""
    common: CommonInfo
    image_info: Optional[Any]
    video_info: Optional[VideoInfo]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式，用于API调用"""
        return asdict(self)

    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class XiaohongshuNoteBuilder:
    """小红书笔记构建器，用于简化笔记创建过程"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """重置构建器"""
        self._note_data = {
            'common': {
                'type': 'video',
                'note_id': '',
                'source': '{"type":"web","ids":"","extraInfo":"{\\"systemId\\":\\"ark\\"}"}',
                'title': '',
                'desc': '',
                'ats': [],
                'hash_tag': [],
                'business_binds': '{"version":1,"noteId":0,"bizType":0,"noteOrderBind":{},"notePostTiming":{},"noteCollectionBind":{"id":""}}',
                'privacy_info': {'op_type': 1, 'type': 0},
                'goods_info': {'extension': {'live_preheat': '0'}},
                'biz_relations': []
            },
            'image_info': None,
            'video_info': None
        }
        return self
    
    def set_title(self, title: str):
        """设置标题"""
        self._note_data['common']['title'] = title
        return self
    
    def set_description(self, desc: str):
        """设置描述"""
        self._note_data['common']['desc'] = desc
        return self
    
    def add_hashtag(self, tag_id: str, name: str, link: str):
        """添加话题标签"""
        hashtag = {
            'id': tag_id,
            'name': name,
            'link': link,
            'type': 'topic'
        }
        self._note_data['common']['hash_tag'].append(hashtag)
        return self
    
    def set_video_info(self, video: Video):
        """设置视频信息"""
        # 设置视频信息
        video_metadata = {
            "video": {
                "bitrate": video.bitrate,
                "colour_primaries": video.colour_primaries,
                "duration": video.duration,
                "format": video.format,
                "frame_rate": video.frame_rate,
                "height": video.height,
                "matrix_coefficients": video.matrix_coefficients,
                "rotation": video.rotation,
                "transfer_characteristics": video.transfer_characteristics,
                "width": video.width
            },
            "audio": {
                "bitrate": video.audio_bitrate,
                "channels": video.audio_channels,
                "duration": video.audio_duration,
                "format": video.audio_format,
                "sampling_rate": video.audio_sampling_rate
            }
        }
        video_info = {
            "fileid": video.file_id,
            "file_id": video.file_id,
            "format_width": video.width,
            "format_height": video.height,
            "video_preview_type": "full_vertical_screen",
            "composite_metadata": video_metadata,
            "timelines": [],
            "cover": {
                "fileid": video.cover_file_id,
                "file_id": video.cover_file_id,
                "height": video.cover_height,
                "width": video.cover_width,
                "frame": {
                    "ts": 0,                    # 时间戳：第0秒作为封面
                    "is_user_select": False,    # 是否用户选择：系统自动选择
                    "is_upload": False          # 是否上传的封面：系统生成
                }
            },
            "chapters": [],
            "chapter_sync_text": False,
            "segments": {
                "count": 1,
                "need_slice": False,
                "items": [
                    {
                        "mute": 0,
                        "speed": 1,
                        "start": 0,
                        "duration": float(video.duration) / 1000,
                        "transcoded": 0,
                        "media_source": 1,
                        "original_metadata": video_metadata
                    }
                ]
            },
            "entrance": "web"
        }
        self._note_data['video_info'] = video_info
        return self
    
    def add_biz_relation(self, biz_type: str, biz_id: str, extra_info: str):
        """添加业务关系"""
        relation = {
            'biz_type': biz_type,
            'biz_id': biz_id,
            'extra_info': extra_info
        }
        self._note_data['common']['biz_relations'].append(relation)
        return self
    
    def build(self) -> Dict[str, Any]:
        """构建最终的笔记数据"""
        return self._note_data.copy() 