import logging
from typing import Dict, Any, Optional, Tuple, Generator, List
from datetime import datetime
import pytz
import xmltodict
import json
from sqlmodel import select, Session
from app.internal.db import engine
from app.models.video import Video

from app.services.xiaohongshu.xiaohongshu_client import XiaohongshuClient, XiaohongshuConfig
from app.models.xiaohongshu import XiaohongshuNoteBuilder
from app.models.product import ProductArticle, ArticleStatus, Tag, ArticleVideoMapping
from app.config.auth_config import AuthConfig
from app.services.oss_service import OSSService
import xml.etree.ElementTree as ET
import requests

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
                # 添加 autoPlayMedioBack=yes 参数到链接
                link = tagInfo["link"]
                if "?" in link:
                    link += "&autoPlayMedioBack=yes"
                else:
                    link += "?autoPlayMedioBack=yes"
                builder.add_hashtag(tagInfo["id"], tagInfo["name"], link)

    def _get_upload_permit(self, scene: str = "video") -> Tuple[str, str, str]:
        """
        获取上传许可
        """
        params = {"biz_name": "spectrum", "scene": scene, "file_count": 1, "version": "1", "source": "web"}
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
    
    def _upload_chunk(self, upload_addr: str, token: str, file_id: str, upload_id: str, chunk_stream: Generator[bytes, None, None], file_info: dict) -> List[Dict[str, str]]:
        """
        上传分块
        
        Args:
            upload_addr: 上传地址
            token: 上传token
            file_id: 文件ID
            upload_id: 上传ID
            chunk_stream: 文件块生成器
            file_info: 文件信息
            
        Returns:
            List[Dict[str, str]]: 每个分片的信息，包含 PartNumber 和 ETag
        """
        etags = []
        try:
            for part_number, chunk in enumerate(chunk_stream, 1):
                self.logger.info(f"Uploading part {part_number}/{file_info['total_chunks']}")
                
                # 构造分片上传请求参数
                params = {
                    "partNumber": part_number,
                    "uploadId": upload_id
                }
                
                # 获取当前分片的大小
                chunk_size = len(chunk)
                
                # # 发送分片上传请求 这样发送会超时
                # response = self.client._make_request(
                #     "PUT",
                #     f"/{file_id}",
                #     api_base_url=f"https://{upload_addr}",
                #     params=params,
                #     headers={
                #         "content-type": "application/octet-stream",
                #         "content-length": str(chunk_size),
                #         "x-cos-security-token": token,
                #     },
                #     data=chunk,
                #     stream=True,
                #     need_sign=False
                # )
                url = f"https://{upload_addr}/{file_id}"
                headers = {
                    "content-type": "application/octet-stream",
                    "content-length": str(chunk_size),
                    "x-cos-security-token": token
                }

                # 使用requests直接发送二进制数据
                response = requests.put(
                    url,
                    params=params,
                    headers=headers,
                    data=chunk,  # 直接发送二进制数据
                    stream=True  # 使用流式传输
                )
                
                # 获取ETag
                etag = response.headers.get("ETag")
                if not etag:
                    raise Exception(f"Failed to upload part {part_number}, no ETag in response")
                
                # 记录分片信息
                etags.append({
                    "PartNumber": str(part_number),
                    "ETag": etag
                })
                
                self.logger.info(f"Successfully uploaded part {part_number}, size: {chunk_size}, ETag: {etag}")
                
            return etags
            
        except Exception as e:
            self.logger.error(f"Failed to upload chunks: {str(e)}")
            raise

    def _upload_confirm(self, upload_addr: str, token: str, file_id: str, upload_id: str, etags: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        完成分片上传
        
        Args:
            upload_addr: 上传地址
            token: 上传token
            file_id: 文件ID
            upload_id: 上传ID
            etags: 分片的ETag列表
            
        Returns:
            Dict[str, Any]: 上传结果
        """
        try:
            # 完成上传
            complete_xml = self._build_complete_xml(etags)
            
            # 使用requests直接发送完成请求
            url = f"https://{upload_addr}/{file_id}"
            params = {
                "uploadId": upload_id
            }
            headers = {
                "content-type": "application/xml",
                "x-cos-security-token": token
            }
            
            self.logger.info(f"Sending complete request with XML: {complete_xml}")
            response = requests.post(
                url,
                params=params,
                headers=headers,
                data=complete_xml.encode('utf-8')  # 确保发送UTF-8编码的字节
            )
            
            if response.status_code != 200:
                raise Exception(f"Complete upload failed with status {response.status_code}: {response.text}")
            
            # 解析响应
            result = xmltodict.parse(response.text)
            
            if "CompleteMultipartUploadResult" not in result:
                raise Exception(f"Invalid complete response: {response.text}")
            
            complete_result = result["CompleteMultipartUploadResult"]
            return {
                "file_id": complete_result.get("Key", ""),
                "etag": complete_result.get("ETag", "")
            }
        except Exception as e:
            self.logger.error(f"Failed to complete upload: {str(e)}")
            raise

    def upload_video_to_xiaohongshu(self, file_stream: Generator[bytes, None, None], file_info: dict) -> Dict[str, Any]:
        """
        上传视频到小红书
        """
        try:
            # 获取上传许可
            upload_addr, token, file_id = self._get_upload_permit()
            if not upload_addr or not token or not file_id:
                self.logger.error(f"获取上传许可失败: {upload_addr}, {token}, {file_id}")
                raise
            
            # 初始化上传分块
            self._init_upload_chunk(upload_addr, token, file_id)
            
            # 初始化上传桶
            upload_id = self._init_upload_bucket(upload_addr, token, file_id)
            self.logger.info(f"初始化上传桶成功: {upload_id}")
            if not upload_id:
                self.logger.error(f"初始化上传桶失败: {upload_id}")
                raise
            
            # 上传分片
            etags = self._upload_chunk(upload_addr, token, file_id, upload_id, file_stream, file_info)
            
            # 完成上传
            return self._upload_confirm(upload_addr, token, file_id, upload_id, etags)
            
        except Exception as e:
            self.logger.error(f"Failed to upload video: {str(e)}")
            raise

    def _upload_cover(self, upload_addr: str, token: str, file_id: str, cover: str) -> str:
        """
        上传封面
        """
        file_data = requests.get(cover).content
        url = f"https://{upload_addr}/{file_id}"
        headers = {
            "content-length": str(len(file_data)),
            "x-cos-security-token": token
        }

        # 使用requests直接发送二进制数据
        response = requests.put(
            url,
            headers=headers,
            data=file_data,  # 直接发送二进制数据
            stream=True  # 使用流式传输
        )

        if response.status_code != 200:
            raise Exception(f"Failed to upload cover: {response.text}")
        self.logger.info(f"上传封面成功: {file_id}")
        return file_id

    def upload_cover_to_xiaohongshu(self, cover: str) -> str:
        """
        上传封面到小红书
        """
        try:
            # 获取上传许可
            upload_addr, token, file_id = self._get_upload_permit(scene="image")
            if not upload_addr or not token or not file_id:
                self.logger.error(f"封面上传获取上传许可失败: {upload_addr}, {token}, {file_id}, {cover}")
                raise
            
            # 上传
            self._upload_cover(upload_addr, token, file_id, cover)
            return file_id
            
        except Exception as e:
            self.logger.error(f"Failed to upload cover: {str(e)}")
            raise

    def _build_complete_xml(self, parts: List[Dict[str, str]]) -> str:
        """构建完成上传的XML请求体"""
        # 手动构建XML声明，确保格式完全匹配
        xml_declaration = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        
        root = ET.Element('CompleteMultipartUpload')
        for part in sorted(parts, key=lambda x: int(x["PartNumber"])):
            part_elem = ET.SubElement(root, 'Part')
            part_number = ET.SubElement(part_elem, 'PartNumber')
            part_number.text = part["PartNumber"]
            etag = ET.SubElement(part_elem, 'ETag')
            etag.text = part["ETag"]
        
        # 不使用ET的xml_declaration，而是手动拼接
        body = ET.tostring(root, encoding='UTF-8', xml_declaration=False).decode('utf-8')
        return xml_declaration + body

    def send_note(self, article_data: ProductArticle, goods_id: str, goods_name: str, note_data: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, Any], Video]:
        """
        发送笔记到小红书
        
        Args:
            article_data: 文章数据
            goods_id: 商品ID
            goods_name: 商品名称
            note_data: 笔记数据，如果为None则使用示例数据
            
        Returns:
            Tuple[Dict[str, Any], Video]: 
                - Dict[str, Any]: API响应结果，包含 success 字段表示是否成功
                - Video: 使用的视频对象
        """
        builder = XiaohongshuNoteBuilder()
        
        # 设置基本信息
        builder.set_title(article_data.title)
        tags = article_data.tags.split(",")
        description = f"{article_data.content}\n\n"
        for tag in tags:
            description += f"#{tag}[话题]# "
        builder.set_description(description)
        
         # 获取视频信息
        with Session(engine) as session:
            video = session.exec(
                select(Video).where(Video.sku_id == goods_id, Video.is_enabled == True)
            ).first()
            self.logger.info(f"视频信息: {video}")    
            if not video:
                self.logger.info(f"没有找到可用视频: {goods_id}")
                return {"success": False, "message": "没有找到可用视频"}, None
            
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
        
       
        
            # 上传视频到小红书
        oss_service = OSSService(logger=self.logger)
        file_stream, file_info = oss_service.get_file_stream(video.oss_object_key, chunk_size=3 * 1024 * 1024)
        self.logger.info(f"文件信息: {file_info}")
        upload_result = self.upload_video_to_xiaohongshu(file_stream, file_info)
        video.third_file_id = upload_result.get("file_id", "")

        style = f"video/snapshot,t_1000,f_jpg,w_{video.width},h_{video.height},m_fast"
        cover = oss_service.bucket.sign_url("GET", video.oss_object_key, 3600, params={"x-oss-process": style})
        file_id = self.upload_cover_to_xiaohongshu(cover)
        video.cover_file_id = file_id

        # 设置视频信息
        builder.set_video_info(video)
        
        note_data = builder.build()
        self.logger.info(f"笔记数据: {note_data}")
            
        try:
            self.logger.info("开始发送笔记")
            response = self.client._make_request("POST", "/web_api/sns/v2/note", api_base_url="https://edith.xiaohongshu.com", data=note_data)
            self.logger.info("笔记发送完成")
            return response, video
        except Exception as e:
            self.logger.error(f"发送笔记失败: {str(e)}")
            return {"success": False, "message": str(e)}, video
    
    def close(self):
        """关闭服务"""
        self.client.close() 