"""
路由模块初始化文件
"""

from .health import router as health_router
from .auth import router as auth_router
from .admin import router as admin_router
from .products import router as products_router
from .articles import router as articles_router
from .videos import router as videos_router
from .system_settings import router as system_settings_router
from .publish_config import router as publish_config_router
from .prompt_template import router as prompt_template_router

# Export all routers
__all__ = [
    "health_router",
    "auth_router",
    "admin_router",
    "products_router",
    "articles_router",
    "videos_router",
    "system_settings_router",
    "publish_config_router",
    "prompt_template_router",
]
