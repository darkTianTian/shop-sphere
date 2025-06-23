import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
import pytz
import xmltodict
import json
from sqlmodel import select, Session
from app.internal.db import engine
from app.models.video import Video

from app.services.xiaohongshu.xiaohongshu_client import XiaohongshuClient, XiaohongshuConfig
from app.models.xiaohongshu import XiaohongshuNoteBuilder
from app.models.product import ProductArticle, ArticleStatus, Tag
from app.config.auth_config import AuthConfig


class NoteService:
    """笔记发送服务"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.client = XiaohongshuClient(logger=self.logger)

    def set_topic_tags(self, article_data: ProductArticle, builder: XiaohongshuNoteBuilder):
        """
        设置话题标签
        """
        for tag in article_data.tags.split(","):
            params = {"keyword":tag,"suggest_topic_request":{"title":"","desc":""},"page":{"page_size":20,"page":1}}
            response = self.client._make_request("POST", "/web_api/sns/v1/search/topic", api_base_url="https://edith.xiaohongshu.com", data=params)
            if tagsInfo := response["data"].get("topic_info_dtos", []):
                tagInfo = tagsInfo[0]
                builder.add_hashtag(tagInfo["id"], tagInfo["name"], tagInfo["link"])

    def _get_upload_permit(self) -> Tuple[str, str, str]:
        """
        获取上传许可
        """
        params = {"biz_name": "spectrum", "scene": "video", "file_count": 1, "version": "1", "source": "web"}
        response = self.client._make_request("GET", "/api/media/v1/upload/creator/permit", api_base_url="https://creator.xiaohongshu.com", params=params)
        if upload_permits:=response["data"].get("uploadTempPermits", []):
            upload_permit = upload_permits[0]
            self.logger.info(f"上传许可: {upload_permit}")
            return upload_permit['uploadAddr'], upload_permit['token'], upload_permit['fileIds'][0]
        else:
            self.logger.error(f"获取上传许可失败: {response}")
            return None, None, None
        
    def _init_upload_chunk(self, upload_addr: str, token: str, file_id: str) -> Dict[str, Any]:
        """
        初始化上传分块
        """
        params = {"uploads":"", "prefix": file_id}
        response = self.client._make_request("GET", "", api_base_url=f"https://{upload_addr}",
                                              params=params, headers={"x-cos-security-token": token}, reponse_format="xml")
        self.logger.info(f"初始化上传分块响应: {response}")
        return response
    
    def _init_upload_bucket(self, upload_addr: str, token: str, file_id: str) -> str:
        """
        初始化上传桶
        """
        params = {"uploads":""}
        response = self.client._make_request("POST", "/"+file_id, api_base_url=f"https://{upload_addr}",
                                              params=params, headers={"x-cos-security-token": token}, reponse_format="xml")
        self.logger.info(f"初始化上传桶响应: {response}")
        return response.get("InitiateMultipartUploadResult", {}).get("UploadId", "")

    def upload_video_to_xiaohongshu(self, video_data: Video) -> Dict[str, Any]:
        """
        上传视频到小红书
        """
        # 获取上传许可
        upload_addr, token, file_id = self._get_upload_permit()
        if not upload_addr or not token or not file_id:
            self.logger.error(f"获取上传许可失败: {upload_addr}, {token}, {file_id}")
            return {}
        self._init_upload_chunk(upload_addr, token, file_id)
        
        upload_id = self._init_upload_bucket(upload_addr, token, file_id)
        self.logger.info(f"初始化上传桶成功: {upload_id}")
        if not upload_id:
            self.logger.error(f"初始化上传桶失败: {upload_id}")
            return {}
        
        
    def send_note(self, article_data: ProductArticle, goods_id: str, goods_name: str, note_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
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

        
        builder = XiaohongshuNoteBuilder()
        
        # 设置基本信息
        builder.set_title(article_data.title)  
        # builder.set_description('''养猫的铲屎官们，是不是还在为主子的"破坏力"发愁？沙发、椅子、桌腿无一幸免，换了不少猫抓板却总是不耐用、不防滑？🙃别担心，今天推荐一款全能的剑麻猫抓板，让主子抓得开心、玩得尽兴、睡得舒适，一块顶三块！🎉\t\n\t\n🌟 优质剑麻材质：这款猫抓板采用天然剑麻细密编织，抓挠起来非常舒适，既不伤爪也不会掉毛～而且超级耐用，抓再久也不会变形，简直是猫主子的抓挠理想型！🐾\t\n\t\n🌟 贴心防滑设计：抓板底部设计了防滑垫，不管是放在瓷砖地板、木地板还是地毯上，都能稳稳地贴合地面，再也不用担心主子抓挠时抓板滑来滑去，简直省心又放心！🎯\t\n\t\n🌟 逗猫球太加分：这款抓板自带一个逗猫球，主子一看到就挪不开爪子，一会儿拨球、一会儿抓挠，玩得根本停不下来～抓累了还能直接趴在抓板上睡觉，真的是抓、玩、睡一站式服务，性价比爆棚！💰\t\n\t\n✨ 实际体验：买了这款剑麻抓板之后，我家主子再也不抓沙发了，天天围着抓板抓个不停，玩逗猫球玩得特别起劲～而且抓板防滑又耐用，我根本不用担心它乱跑或者散架～最治愈的是，看着主子玩累了呼呼睡觉的模样，铲屎官心里都被暖化了！😍\t\n\t\n铲屎官们，别再犹豫啦！🎁 快给主子安排上这款超实用的剑麻抓板吧～让主子玩得尽兴，铲屎官更省心！❤️\t\n\t\n\n #猫咪用品分享[话题]#  #猫咪自嗨玩具[话题]#  #铲屎官必备[话题]#  #剑麻猫抓板[话题]#  #好物分享[话题]#  #猫窝推荐[话题]# ''')
        builder.set_description(article_data.content)

        # 设置文章的话题标签
        self.set_topic_tags(article_data, builder)

        # 设置商品信息
        extra_info = {
            'goods_id': goods_id,
            'goods_name': goods_name,
            'goods_type': 'goods_seller',
            'tab_id': 1,
            'image_type': 'spec',
            'left_bottom_type': 'BUY_GOODS',
            'bind_order': 0
            }
        builder.add_biz_relation(
            biz_type="GOODS_SELLER_V2",
            biz_id=goods_id,
            extra_info=json.dumps(extra_info)
        )
        
        # 获取视频信息
        # TODO:这里sku_id为空
        with Session(engine) as session:
            video = session.exec(
                select(Video).where(Video.sku_id == goods_id, Video.is_enabled == True)
            ).first()
            self.logger.info(f"视频信息: {video}")    
            if not video:
                self.logger.error(f"没有找到可用视频: {goods_id}")
                return {}
        
        # 上传视频到小红书
        self.upload_video_to_xiaohongshu(video)
        
        # 设置视频信息
        builder.set_video_info(video)
        
        note_data = builder.build()

        self.logger.info(f"笔记数据: {note_data}")
            
        try:
            self.logger.info("开始发送笔记")
            # response = self.client._make_request("POST", "/web_api/sns/v2/note", api_base_url="https://edith.xiaohongshu.com", data=note_data)
            self.logger.info("笔记发送完成")
            # return response
        except Exception as e:
            self.logger.error(f"发送笔记失败: {str(e)}")
            raise
    
    def close(self):
        """关闭服务"""
        self.client.close() 