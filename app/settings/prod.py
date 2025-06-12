from app.settings.base import BaseSettings, DatabaseSettings

class Settings(BaseSettings):
    """生产环境配置"""
    
    @classmethod
    def get_db_settings(cls) -> DatabaseSettings:
        """获取生产环境数据库配置"""
        # 生产环境使用环境变量中的配置
        return super().get_db_settings()

TIMEZONE = 'Asia/Shanghai'
# 其他本地环境相关配置可在此添加