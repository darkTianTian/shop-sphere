from app.routers.health import router as health_router
from app.routers.auth import router as auth_router
from app.routers.admin import router as admin_router
from app.routers.products import router as products_router
from app.routers.articles import router as articles_router
from app.routers.videos import router as videos_router

__all__ = [
    'health_router',
    'auth_router',
    'admin_router',
    'products_router',
    'articles_router',
    'videos_router'
]
