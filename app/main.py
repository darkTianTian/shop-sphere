from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers import video, health, auth, admin
from app.settings import load_settings
from app.middleware.admin_auth import AdminAuthMiddleware

app = FastAPI(
    title="ShopSphere API",
    description="ShopSphere 电商管理系统 API",
    version="0.1.0",
)

# 加载配置
settings = load_settings()

# 添加管理后台权限验证中间件（最外层）
app.add_middleware(AdminAuthMiddleware)

# 配置会话（中间层）
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    max_age=3600 * 24 * 7,  # 7天
)

# 添加CORS中间件（最内层）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# 包含路由
app.include_router(video.router)
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(admin.router)


@app.get("/")
def read_root():
    return {
        "message": "Shop Sphere API", 
        "auth_docs": "/docs#/auth",
        "admin_login": "/admin/login",
        "api_docs": "/docs"
    } 