import os
import uuid
import logging
import hashlib
from datetime import datetime
from typing import Optional, Tuple, Generator
import oss2
from app.config.oss_config import OSSConfig
import time
import math


class OSSService:
    """阿里云OSS文件上传服务"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.config = OSSConfig
        
        if not self.config.is_configured():
            self.logger.warning("OSS配置不完整，将使用本地存储")
            self.bucket = None
            self.internal_bucket = None
        else:
            # 初始化OSS客户端
            auth = oss2.Auth(self.config.ACCESS_KEY_ID, self.config.ACCESS_KEY_SECRET)
            
            # 使用公网endpoint用于签名URL
            endpoint = self.config.ENDPOINT
            self.logger.info(f"使用OSS公网endpoint: {endpoint}")
            self.bucket = oss2.Bucket(auth, endpoint, self.config.BUCKET_NAME)
            
            # 使用内网endpoint用于上传（如果在阿里云ECS上）
            if os.getenv("SERVER_ENVIRONMENT") == "PROD":
                internal_endpoint = endpoint.replace(".aliyuncs.com", "-internal.aliyuncs.com")
                self.logger.info(f"使用OSS内网endpoint: {internal_endpoint}")
                self.internal_bucket = oss2.Bucket(auth, internal_endpoint, self.config.BUCKET_NAME)
            else:
                self.internal_bucket = self.bucket
            
            # 配置重试
            for b in [self.bucket, self.internal_bucket]:
                if b:
                    b.enable_crc = False  # 禁用CRC校验以提高性能
                    b.connect_timeout = 20  # 连接超时时间（秒）
                    b.read_timeout = 30  # 读取超时时间（秒）
                    # 设置重试策略
                    b.max_retries = 3  # 最大重试次数
                    b.retry_delay = 1  # 初始重试延迟（秒）
    
    def is_available(self) -> bool:
        """检查OSS服务是否可用"""
        return self.bucket is not None and self.internal_bucket is not None
    
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
    
    def upload_file(self, file_content: bytes, filename: str, content_type: str = None, *, prefix: str = None, file_hash: str = None) -> Tuple[bool, str, str]:
        """
        上传文件到OSS
        
        Args:
            file_content: 文件内容（字节）
            filename: 原始文件名
            content_type: 文件MIME类型
            prefix: 文件路径前缀
            file_hash: 文件SHA256哈希值，如果不提供则不会存储在元数据中
            
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
            
            # 生成对象键名
            object_key = self.generate_object_key(filename, file_hash or "", prefix=prefix)
            
            # 设置上传参数
            headers = {
                'Content-Type': content_type if content_type else 'application/octet-stream',
            }
            if file_hash:
                headers['x-oss-meta-hash'] = file_hash  # 将哈希值存储在元数据中
            
            # 上传文件（带重试）
            max_retries = 3
            retry_count = 0
            while retry_count < max_retries:
                try:
                    # 使用内网bucket上传
                    result = self.internal_bucket.put_object(object_key, file_content, headers=headers)
                    self.logger.info(f"status code: {result.status}, request_id: {result.request_id}")
                    
                    if result.status == 200:
                        # 生成公网访问URL
                        public_url = self.config.get_public_url(object_key)
                        self.logger.info(f"文件上传成功: {filename} -> {object_key}, hash: {file_hash or 'none'}")
                        return True, object_key, public_url
                    else:
                        self.logger.error(f"文件上传失败: {filename}, 状态码: {result.status}")
                        retry_count += 1
                except Exception as e:
                    error_details = str(e)
                    self.logger.error(f"上传出错 (重试 {retry_count + 1}/{max_retries}): {error_details}")
                    retry_count += 1
                    if retry_count < max_retries:
                        # 指数退避，但设置最大延迟
                        delay = min(self.internal_bucket.retry_delay * (2 ** retry_count), 30)
                        self.logger.info(f"等待 {delay} 秒后重试...")
                        time.sleep(delay)
                    continue
            
            return False, f"上传失败（已重试{max_retries}次）: {error_details}", ""
                
        except Exception as e:
            self.logger.error(f"文件上传异常: {filename}, 错误: {str(e)}")
            return False, f"上传异常: {str(e)}", ""
    
    def upload_temp_file(self, temp_file_path: str, original_filename: str, content_type: str = None, *, prefix: str = None, file_hash: str = None) -> Tuple[bool, str, str]:
        """
        上传临时文件到OSS
        
        Args:
            temp_file_path: 临时文件路径
            original_filename: 原始文件名
            content_type: 文件MIME类型
            prefix: 文件路径前缀
            file_hash: 文件SHA256哈希值，如果不提供则不会存储在元数据中
            
        Returns:
            (是否成功, 错误信息或对象键名, 公网访问URL)
        """
        try:
            with open(temp_file_path, 'rb') as f:
                file_content = f.read()
            return self.upload_file(file_content, original_filename, content_type, prefix=prefix, file_hash=file_hash)
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

    def get_file_stream(self, oss_object_key: str, chunk_size: int = 5 * 1024 * 1024) -> Tuple[Generator[bytes, None, None], dict]:
        """
        获取文件流和文件信息，用于分块上传
        
        Args:
            oss_object_key: OSS对象的键名
            chunk_size: 分块大小，默认5MB
            
        Returns:
            Tuple[Generator, dict]: (文件流生成器, 文件信息)
            文件信息包含：
            {
                'size': 文件大小,
                'content_type': 内容类型,
                'name': 文件名,
                'total_chunks': 总分块数
            }
        """
        try:
            # 获取bucket实例
            bucket = self.internal_bucket if os.getenv("SERVER_ENVIRONMENT") == "PROD" else self.bucket
            if not bucket:
                raise Exception("OSS bucket not configured")
            
            # 获取文件元信息
            object_meta = bucket.head_object(oss_object_key)
            file_size = object_meta.content_length
            content_type = object_meta.content_type
            file_name = os.path.basename(oss_object_key)
            total_chunks = math.ceil(file_size / chunk_size)

            self.logger.info(f"Preparing to stream file: {oss_object_key}")
            self.logger.info(f"File size: {file_size / 1024 / 1024:.2f}MB, Total chunks: {total_chunks}")

            def chunk_generator() -> Generator[bytes, None, None]:
                """生成文件块的生成器"""
                current_position = 0
                while current_position < file_size:
                    # 计算当前块的大小
                    current_chunk_size = min(chunk_size, file_size - current_position)
                    
                    # 使用range下载当前块
                    chunk = bucket.get_object(
                        oss_object_key,
                        byte_range=(current_position, current_position + current_chunk_size - 1)
                    ).read()
                    
                    yield chunk
                    
                    current_position += current_chunk_size
                    self.logger.debug(f"Streamed {current_position}/{file_size} bytes ({(current_position/file_size*100):.1f}%)")

            file_info = {
                'size': file_size,
                'content_type': content_type,
                'name': file_name,
                'total_chunks': total_chunks
            }

            return chunk_generator(), file_info

        except oss2.exceptions.NoSuchKey:
            error_msg = f"File not found in OSS: {oss_object_key}"
            self.logger.error(error_msg)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Failed to get file stream from OSS: {str(e)}"
            self.logger.error(error_msg)
            raise 