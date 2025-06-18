from typing import Union

from fastapi import FastAPI
from app.routers import video, health

app = FastAPI(
    title="Shop Sphere API",
    description="电商平台API，支持视频素材上传和处理",
    version="1.0.0"
)

# 包含路由器
app.include_router(video.router)
app.include_router(health.router)


@app.get("/")
def read_root():
    return {"Hello": "World", "message": "Shop Sphere API is running"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    return {"item_id": item_id, "q": q} 