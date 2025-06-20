import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class DatabaseSettings:
    """数据库配置"""
    host: str
    port: int
    database: str
    user: str
    password: str
    
    @property
    def url(self) -> str:
        """获取数据库连接URL"""
        return f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

class BaseSettings:
    """基础配置类"""
    TIMEZONE = 'Asia/Shanghai'
    
    # 安全配置
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-jwt-secret-key-change-in-production')
    
    def get_db_settings(self) -> DatabaseSettings:
        """获取数据库配置"""
        return DatabaseSettings(
            host=os.environ.get('DB_HOST') or os.environ.get('MYSQL_HOST', 'localhost'),
            port=int(os.environ.get('DB_PORT') or os.environ.get('MYSQL_PORT', '3306')),
            database=os.environ.get('DB_NAME') or os.environ.get('MYSQL_DATABASE', 'shopsphere'),
            user=os.environ.get('DB_USER') or os.environ.get('MYSQL_USER', 'shopsphere'),
            password=os.environ.get('DB_PASSWORD') or os.environ.get('MYSQL_PASSWORD', 'shopsphere123')
        ) 