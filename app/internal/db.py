from sqlmodel import SQLModel, create_engine
from app.settings import load_settings
# 导入所有模型以确保它们被注册到 SQLModel 元数据中
from app.models.video import VideoMaterial

def init_db():
    """初始化数据库，创建所有表"""
    settings = load_settings()
    db_settings = settings.Settings.get_db_settings()
    engine = create_engine(db_settings.url, echo=False)
    
    # 创建所有表
    SQLModel.metadata.create_all(engine)
    
    return engine

# 全局数据库引擎
engine = init_db() 