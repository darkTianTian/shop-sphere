import os
import uuid
import logging
import hashlib
from datetime import datetime
from typing import Optional, Tuple
import oss2
from app.config.oss_config import OSSConfig
import time


class OSSService:
    """阿里云OSS文件上传服务"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.config = OSSConfig
        
        if not self.config.is_configured():
            self.logger.warning("OSS配置不完整，将使用本地存储")
            self.bucket = None
        else:
            # 初始化OSS客户端
            auth = oss2.Auth(self.config.ACCESS_KEY_ID, self.config.ACCESS_KEY_SECRET)
            # 使用内部endpoint
            endpoint = self.config.get_internal_endpoint()
            self.bucket = oss2.Bucket(auth, endpoint, self.config.BUCKET_NAME)
            # 配置重试
            self.bucket.enable_crc = False  # 禁用CRC校验以提高性能
            self.bucket.connection_timeout = 120  # 连接超时时间（秒）
            self.bucket.max_retries = 5  # 最大重试次数
    
    def is_available(self) -> bool:
        """检查OSS服务是否可用"""
        return self.bucket is not None
    
    def calculate_file_hash(self, file_content: bytes) -> str:
        """
        计算文件内容的SHA256哈希值
        
        Args:
            file_content: 文件内容（字节）
            
        Returns:
            文件的SHA256哈希值
        """
        return hashlib.sha256(file_content).hexdigest()

    def generate_object_key(self, filename: str, file_hash: str, prefix: str = None) -> str:
        """
        生成OSS对象键名
        
        Args:
            filename: 原始文件名
            file_hash: 文件哈希值
            prefix: 前缀路径，默认使用配置中的VIDEO_PREFIX
            
        Returns:
            生成的对象键名
        """
        if prefix is None:
            prefix = self.config.VIDEO_PREFIX
            
        # 获取文件扩展名
        _, ext = os.path.splitext(filename)
        
        # 生成唯一文件名：日期 + 哈希值前8位 + 扩展名
        date_str = datetime.now().strftime("%Y%m%d%H%M%S")
        hash_prefix = file_hash[:8]
        new_filename = f"{hash_prefix}_{date_str}{ext}"
        
        return f"{prefix}{new_filename}"
    
    def upload_file(self, file_content: bytes, filename: str, content_type: str = None) -> Tuple[bool, str, str]:
        """
        上传文件到OSS
        
        Args:
            file_content: 文件内容（字节）
            filename: 原始文件名
            content_type: 文件MIME类型
            
        Returns:
            (是否成功, 错误信息或对象键名, 公网访问URL)
        """
        if not self.is_available():
            return False, "OSS服务未配置或不可用", ""
        
        try:
            # 检查文件大小
            if len(file_content) > self.config.MAX_FILE_SIZE:
                return False, f"文件大小超过限制({self.config.MAX_FILE_SIZE // (1024*1024)}MB)", ""
            
            # 检查文件扩展名
            _, ext = os.path.splitext(filename)
            if ext.lower() not in self.config.ALLOWED_VIDEO_EXTENSIONS:
                return False, f"不支持的文件格式: {ext}", ""
            
            # 计算文件哈希值
            file_hash = self.calculate_file_hash(file_content)
            
            # 生成对象键名
            object_key = self.generate_object_key(filename, file_hash)
            
            # 设置上传参数
            headers = {
                'Content-Type': content_type if content_type else 'application/octet-stream',
                'x-oss-meta-hash': file_hash  # 将哈希值存储在元数据中
            }
            
            # 上传文件（带重试）
            max_retries = 3
            retry_count = 0
            while retry_count < max_retries:
                try:
                    result = self.bucket.put_object(object_key, file_content, headers=headers)
                    self.logger.info(f"status code: {result.status}, request_id: {result.request_id}")
                    
                    if result.status == 200:
                        # 生成公网访问URL
                        public_url = self.config.get_public_url(object_key)
                        self.logger.info(f"文件上传成功: {filename} -> {object_key}, hash: {file_hash}")
                        return True, object_key, public_url
                    else:
                        self.logger.error(f"文件上传失败: {filename}, 状态码: {result.status}")
                        retry_count += 1
                except Exception as e:
                    self.logger.error(f"上传出错 (重试 {retry_count + 1}/{max_retries}): {str(e)}")
                    retry_count += 1
                    if retry_count < max_retries:
                        time.sleep(2 ** retry_count)  # 指数退避
                    continue
            
            return False, f"上传失败，已重试{max_retries}次", ""
                
        except Exception as e:
            self.logger.error(f"文件上传异常: {filename}, 错误: {str(e)}")
            return False, f"上传异常: {str(e)}", ""
    
    def upload_temp_file(self, temp_file_path: str, original_filename: str, content_type: str = None) -> Tuple[bool, str, str]:
        """
        上传临时文件到OSS
        
        Args:
            temp_file_path: 临时文件路径
            original_filename: 原始文件名
            content_type: 文件MIME类型
            
        Returns:
            (是否成功, 错误信息或对象键名, 公网访问URL)
        """
        try:
            with open(temp_file_path, 'rb') as f:
                file_content = f.read()
            return self.upload_file(file_content, original_filename, content_type)
        except Exception as e:
            self.logger.error(f"读取临时文件失败: {temp_file_path}, 错误: {str(e)}")
            return False, f"读取文件失败: {str(e)}", ""
    
    def delete_file(self, object_key: str) -> bool:
        """
        删除OSS中的文件
        
        Args:
            object_key: 对象键名
            
        Returns:
            是否删除成功
        """
        if not self.is_available():
            return False
        
        try:
            self.bucket.delete_object(object_key)
            self.logger.info(f"文件删除成功: {object_key}")
            return True
        except Exception as e:
            self.logger.error(f"文件删除失败: {object_key}, 错误: {str(e)}")
            return False 