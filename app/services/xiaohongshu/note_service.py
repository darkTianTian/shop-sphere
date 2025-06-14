import logging
from typing import Dict, Any, Optional
from datetime import datetime
import pytz

from app.services.xiaohongshu.xiaohongshu_client import XiaohongshuClient, XiaohongshuConfig
from app.models.xiaohongshu import XiaohongshuNoteBuilder
from app.config.auth_config import AuthConfig


class NoteService:
    """笔记发送服务"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.client = XiaohongshuClient(logger=self.logger)
        
        
    def send_note(self, note_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        发送笔记
        
        Args:
            note_data: 笔记数据，如果为None则使用示例数据，包含以下字段：
                - title: 笔记标题
                - desc: 笔记描述
                - hash_tags: 话题标签列表，每个标签包含 id, name, type
                - biz_relation: 商品关联信息，包含 biz_type, biz_id, goods_id, goods_name
                - video_info: 视频信息，包含完整的视频元数据
                    - fileid: 视频文件ID
                    - file_id: 视频文件ID（与fileid相同）
                    - format_width: 视频宽度
                    - format_height: 视频高度
                    - video_preview_type: 视频预览类型
                    - composite_metadata: 视频和音频元数据
                    - timelines: 时间线信息
                    - cover: 封面信息
                    - chapters: 章节信息
                    - chapter_sync_text: 章节同步文本
                    - segments: 视频分段信息
                    - entrance: 入口信息
            
        Returns:
            API响应结果
        """
        if note_data is None:
            builder = XiaohongshuNoteBuilder()
            
            # 设置基本信息
            builder.set_title("主子的快乐源泉！防滑猫抓板绝绝子！")
            builder.set_description('''养猫的铲屎官们，是不是还在为主子的"破坏力"发愁？沙发、椅子、桌腿无一幸免，换了不少猫抓板却总是不耐用、不防滑？🙃别担心，今天推荐一款全能的剑麻猫抓板，让主子抓得开心、玩得尽兴、睡得舒适，一块顶三块！🎉\t\n\t\n🌟 优质剑麻材质：这款猫抓板采用天然剑麻细密编织，抓挠起来非常舒适，既不伤爪也不会掉毛～而且超级耐用，抓再久也不会变形，简直是猫主子的抓挠理想型！🐾\t\n\t\n🌟 贴心防滑设计：抓板底部设计了防滑垫，不管是放在瓷砖地板、木地板还是地毯上，都能稳稳地贴合地面，再也不用担心主子抓挠时抓板滑来滑去，简直省心又放心！🎯\t\n\t\n🌟 逗猫球太加分：这款抓板自带一个逗猫球，主子一看到就挪不开爪子，一会儿拨球、一会儿抓挠，玩得根本停不下来～抓累了还能直接趴在抓板上睡觉，真的是抓、玩、睡一站式服务，性价比爆棚！💰\t\n\t\n✨ 实际体验：买了这款剑麻抓板之后，我家主子再也不抓沙发了，天天围着抓板抓个不停，玩逗猫球玩得特别起劲～而且抓板防滑又耐用，我根本不用担心它乱跑或者散架～最治愈的是，看着主子玩累了呼呼睡觉的模样，铲屎官心里都被暖化了！😍\t\n\t\n铲屎官们，别再犹豫啦！🎁 快给主子安排上这款超实用的剑麻抓板吧～让主子玩得尽兴，铲屎官更省心！❤️\t\n\t\n\n #猫咪用品分享[话题]#  #猫咪自嗨玩具[话题]#  #铲屎官必备[话题]#  #剑麻猫抓板[话题]#  #好物分享[话题]#  #猫窝推荐[话题]# ''')
            
            # 设置话题标签
            builder.add_hashtag("5c30b529000000000801372e", "猫咪用品分享", "topic")
            builder.add_hashtag("61ed12ba000000000100051e", "猫咪自嗨玩具", "topic")
            builder.add_hashtag("5bfa9e7c60c92d00011a2506", "铲屎官必备", "topic")
            builder.add_hashtag("615301dd0000000001000ff5", "剑麻猫抓板", "topic")
            builder.add_hashtag("595068c7cd30d86d2938e125", "好物分享", "topic")
            builder.add_hashtag("611f58da0000000001001440", "猫窝推荐", "topic")
            
            # 设置商品信息
            builder.add_biz_relation(
                biz_type="GOODS_SELLER_V2",
                biz_id="6751b6584a1b730001d43a4e",
                extra_info="{\"goods_id\":\"6751b6584a1b730001d43a4e\",\"goods_name\":\"剑麻猫抓板猫窝耐磨不掉屑耐抓麻绳一体猫爪板大号磨爪器猫咪用品 黑色快递袋包装 椭圆麻布款【带耳朵】\",\"goods_type\":\"goods_seller\",\"tab_id\":1,\"image_type\":\"spec\",\"left_bottom_type\":\"BUY_GOODS\",\"bind_order\":0}"
            )
            
            # 设置视频信息
            video_info = {
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
                        "ts": 0,
                        "is_user_select": False,
                        "is_upload": False
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
                            "duration": 22.867,
                            "transcoded": 0,
                            "media_source": 1,
                            "original_metadata": {
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
                            }
                        }
                    ]
                },
                "entrance": "web"
            }
            builder.set_video_info(video_info)
            
            note_data = builder.build()
            
        try:
            self.logger.info("开始发送笔记")
            response = self.client._make_request("POST", "/web_api/sns/v2/note", api_base_url="https://edith.xiaohongshu.com", data=note_data)
            self.logger.info("笔记发送完成")
            return response
        except Exception as e:
            self.logger.error(f"发送笔记失败: {str(e)}")
            raise
    
    def close(self):
        """关闭服务"""
        self.client.close() 