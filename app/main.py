from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.routers import video, health, auth

app = FastAPI(
    title="Shop Sphere API",
    description="商品管理和文章生成系统 - 支持多用户后台管理",
    version="1.0.0"
)

# 添加Session中间件（认证需要）
app.add_middleware(
    SessionMiddleware, 
    secret_key="your-secret-key-change-in-production"
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 包含路由
app.include_router(video.router)
app.include_router(health.router)
app.include_router(auth.router)


@app.get("/")
def read_root():
    return {
        "message": "Shop Sphere API", 
        "auth_docs": "/docs#/auth",
        "admin_login": "/admin/login",
        "api_docs": "/docs"
    } 