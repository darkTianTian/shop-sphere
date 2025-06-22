import os
from typing import Optional

class OSSConfig:
    """阿里云OSS配置"""
    
    # OSS基本配置
    ACCESS_KEY_ID: str = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_ID", "")
    ACCESS_KEY_SECRET: str = os.getenv("ALIBABA_CLOUD_ACCESS_KEY_SECRET", "")
    ENDPOINT: str = os.getenv("OSS_ENDPOINT", "")  # 例如: https://oss-cn-hangzhou.aliyuncs.com
    BUCKET_NAME: str = os.getenv("OSS_BUCKET_NAME", "")
    
    # 文件上传配置
    VIDEO_PREFIX: str = "videos/"  # 视频文件在OSS中的前缀路径
    MAX_FILE_SIZE: int = 200 * 1024 * 1024  # 最大文件大小 200MB
    
    # 允许的视频格式
    ALLOWED_VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv', '.m4v'}
    
    @classmethod
    def is_configured(cls) -> bool:
        """检查OSS是否配置完整"""
        return all([
            cls.ACCESS_KEY_ID,
            cls.ACCESS_KEY_SECRET,
            cls.ENDPOINT,
            cls.BUCKET_NAME
        ])
    
    @classmethod
    def get_internal_endpoint(cls) -> str:
        if not cls.ENDPOINT.startswith('https://'):
            return f"https://{cls.ENDPOINT.replace('http://', '')}"
        return cls.ENDPOINT
    
    @classmethod
    def get_public_url(cls, object_key: str) -> str:
        """获取OSS文件的公网访问URL"""
        # 移除endpoint中的协议部分，构建标准URL
        endpoint_without_protocol = cls.ENDPOINT.replace("https://", "").replace("http://", "")
        # 确保使用HTTPS
        return f"https://{cls.BUCKET_NAME}.{endpoint_without_protocol}/{object_key}" 