from app.settings.base import BaseSettings, DatabaseSettings

class Settings(BaseSettings):
    """本地开发环境配置"""
    
    def get_db_settings(self) -> DatabaseSettings:
        """获取本地数据库配置"""
        return DatabaseSettings(
            host='mysql',  # 使用docker-compose中定义的服务名
            port=3306,
            database='shopsphere',
            user='shopsphere',
            password='shopsphere123'
        )

TIMEZONE = 'Asia/Shanghai'
# 其他本地环境相关配置可在此添加 