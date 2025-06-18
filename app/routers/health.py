from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from sqlmodel import Session
from app.internal.db import engine
import redis
import os
from datetime import datetime

router = APIRouter()

@router.get("/health")
async def health_check():
    """
    健康检查端点
    检查数据库连接、Redis连接和基本服务状态
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "checks": {}
    }
    
    # 检查数据库连接
    try:
        with Session(engine) as session:
            session.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # 检查Redis连接 - 暂时忽略，不影响整体健康状态
    try:
        redis_host = os.getenv("REDIS_HOST", "localhost")
        redis_port = int(os.getenv("REDIS_PORT", "6379"))
        redis_password = os.getenv("REDIS_PASSWORD")
        
        # 创建Redis连接，支持密码
        if redis_password:
            r = redis.Redis(host=redis_host, port=redis_port, password=redis_password, decode_responses=True)
        else:
            r = redis.Redis(host=redis_host, port=redis_port, decode_responses=True)
        
        r.ping()
        health_status["checks"]["redis"] = "healthy"
    except Exception as e:
        health_status["checks"]["redis"] = f"unhealthy: {str(e)} (ignored)"
        # 注释掉这行，不让 Redis 失败影响整体状态
        # health_status["status"] = "unhealthy"
    
    # 检查OSS配置（可选）
    try:
        from app.config.oss_config import OSSConfig
        if OSSConfig.is_configured():
            health_status["checks"]["oss"] = "configured"
        else:
            health_status["checks"]["oss"] = "not_configured"
    except Exception as e:
        health_status["checks"]["oss"] = f"error: {str(e)}"
    
    if health_status["status"] == "unhealthy":
        raise HTTPException(status_code=503, detail=health_status)
    
    return health_status

@router.get("/ready")
async def readiness_check():
    """
    就绪检查端点
    检查应用是否准备好接受请求
    """
    return {"status": "ready", "timestamp": datetime.now().isoformat()} 