from app.settings.base import BaseSettings

class Settings(BaseSettings):
    """生产环境配置"""
    pass  # 使用基类的默认配置

TIMEZONE = 'Asia/Shanghai'
# 其他本地环境相关配置可在此添加