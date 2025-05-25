import requests
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass

from app.models.product import ProductSearchRequest, ProductSearchResponse


@dataclass
class ProductApiConfig:
    """商品API配置"""
    api_url: str = "https://ark.xiaohongshu.com/api/edith/product/search_item_v2"
    timeout: int = 30
    max_retries: int = 3


class ProductClient:
    """商品API客户端"""
    
    def __init__(self, config: Optional[ProductApiConfig] = None, logger: Optional[logging.Logger] = None):
        self.config = config or ProductApiConfig()
        self.logger = logger or logging.getLogger(__name__)
        self.session = requests.Session()
        
    def _get_default_headers(self) -> Dict[str, str]:
        """获取默认请求头"""
        return {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'cache-control': 'no-cache',
            'content-type': 'application/json',
            'origin': 'https://ark.xiaohongshu.com',
            'pragma': 'no-cache',
            'priority': 'u=1, i',
            'referer': 'https://ark.xiaohongshu.com/app-item/list/shelf?from=ark-login',
            'sec-ch-ua': '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.36'
        }
    
    def set_auth_headers(self, authorization: str, x_s: str, x_t: str, cookie: str):
        """设置认证相关的请求头"""
        auth_headers = {
            'authorization': authorization,
            'x-s': x_s,
            'x-t': x_t,
            'x-b3-traceid': '8378add107c3cdbd',  # 可以动态生成
            'Cookie': cookie
        }
        self.session.headers.update(auth_headers)
        
    def search_products(self, request: ProductSearchRequest, custom_headers: Optional[Dict[str, str]] = None) -> ProductSearchResponse:
        """
        搜索商品列表
        
        Args:
            request: 搜索请求对象
            custom_headers: 自定义请求头
            
        Returns:
            商品搜索响应对象
            
        Raises:
            requests.RequestException: 请求异常
        """
        headers = self._get_default_headers()
        if custom_headers:
            headers.update(custom_headers)
            
        payload = request.to_json()
        
        for attempt in range(self.config.max_retries):
            try:
                self.logger.info(f"发送商品搜索请求 (尝试 {attempt + 1}/{self.config.max_retries})")
                self.logger.debug(f"请求参数: {payload}")
                
                response = self.session.post(
                    self.config.api_url,
                    headers=headers,
                    data=payload,
                    timeout=self.config.timeout
                )
                
                # 记录响应状态
                self.logger.info(f"响应状态码: {response.status_code}")
                
                # 尝试解析JSON响应
                try:
                    response_data = response.json()
                    self.logger.debug(f"响应数据: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
                    
                    # 使用数据模型解析响应
                    return ProductSearchResponse.from_dict(response_data)
                    
                except json.JSONDecodeError:
                    self.logger.warning(f"无法解析JSON响应，原始响应: {response.text}")
                    # 返回一个包含原始响应的对象
                    return ProductSearchResponse(
                        success=False,
                        message=f"JSON解析失败: {response.text}",
                        code=response.status_code
                    )
                    
            except requests.exceptions.Timeout:
                self.logger.warning(f"请求超时 (尝试 {attempt + 1}/{self.config.max_retries})")
                if attempt == self.config.max_retries - 1:
                    return ProductSearchResponse(
                        success=False,
                        message="请求超时",
                        code=-1
                    )
                    
            except requests.exceptions.RequestException as e:
                self.logger.error(f"请求异常 (尝试 {attempt + 1}/{self.config.max_retries}): {str(e)}")
                if attempt == self.config.max_retries - 1:
                    return ProductSearchResponse(
                        success=False,
                        message=f"请求异常: {str(e)}",
                        code=-1
                    )
                    
        return ProductSearchResponse(
            success=False,
            message="所有重试尝试都失败了",
            code=-1
        )
    
    def close(self):
        """关闭会话"""
        self.session.close() 