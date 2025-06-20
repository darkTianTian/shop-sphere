"""
管理后台权限验证中间件
"""
from typing import Callable
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse, JSONResponse
from starlette.types import ASGIApp

# 配置日志
logger = logging.getLogger(__name__)

class AdminAuthMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: ASGIApp,
        exclude_paths: set[str] = None
    ):
        super().__init__(app)
        self.exclude_paths = exclude_paths or {
            "/admin/login",
            "/auth/cookie/login",
            "/auth/cookie/logout",
            "/static",
            "/favicon.ico",
            "/docs",
            "/openapi.json"
        }
    
    async def dispatch(self, request: Request, call_next: Callable):
        # 检查是否是管理后台路径
        if not request.url.path.startswith("/admin"):
            return await call_next(request)
            
        # 检查是否是排除的路径
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
            
        # 检查是否是API请求
        is_api_request = request.headers.get("accept") == "application/json"
        
        # 检查用户是否已登录
        try:
            if not hasattr(request, "session"):
                logger.error("Session middleware not initialized")
                if is_api_request:
                    return JSONResponse(
                        status_code=500,
                        content={"detail": "服务器配置错误"}
                    )
                return RedirectResponse(
                    url="/admin/login",
                    status_code=302
                )
            
            user = request.session.get("user")
            if not user:
                logger.info(f"未登录用户尝试访问管理后台: {request.url.path}")
                logger.debug(f"Session内容: {dict(request.session)}")
                if is_api_request:
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "需要登录"}
                    )
                return RedirectResponse(
                    url=f"/admin/login?next={request.url.path}",
                    status_code=302
                )
            
            # 记录访问日志
            logger.info(f"用户 {user.get('username')} 访问: {request.url.path}")
            logger.debug(f"用户信息: {user}")
            
        except AttributeError as e:
            logger.error(f"Session中间件错误: {str(e)}")
            if is_api_request:
                return JSONResponse(
                    status_code=500,
                    content={"detail": "服务器配置错误"}
                )
            return RedirectResponse(
                url="/admin/login",
                status_code=302
            )
        except Exception as e:
            logger.error(f"权限验证错误: {str(e)}")
            if is_api_request:
                return JSONResponse(
                    status_code=500,
                    content={"detail": "服务器内部错误"}
                )
            return RedirectResponse(
                url="/admin/login",
                status_code=302
            )
            
        # 继续处理请求
        return await call_next(request) 