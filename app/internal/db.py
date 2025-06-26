from sqlmodel import SQLModel, create_engine
from app.settings import load_settings
# 导入所有模型以确保它们被注册到 SQLModel 元数据中
from app.models.video import VideoMaterial
from app.models.prompt import AIPromptTemplate
from app.models.user import User  # 添加 User 模型导入
from app.models.publish_config import PublishConfig
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

def init_db():
    """初始化数据库，创建所有表"""
    settings = load_settings()
    db_settings = settings.get_db_settings()
    
    # 使用settings中的配置创建引擎
    engine = create_engine(db_settings.url, echo=False)
    
    # 创建所有表
    SQLModel.metadata.create_all(engine)
    
    return engine

# 初始化数据库并获取同步引擎
engine = init_db()

# 获取数据库配置（用于异步引擎）
settings = load_settings()
db_settings = settings.get_db_settings()

# 创建异步引擎（用于异步操作）
async_engine = create_async_engine(
    db_settings.async_url,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=3600
)

@asynccontextmanager
async def get_async_session():
    """获取异步数据库会话"""
    async with AsyncSession(async_engine) as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise 