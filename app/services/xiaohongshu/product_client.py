import requests
import json
import logging
import time
from typing import Dict, Any, Optional
from .xiaohongshu_client import XiaohongshuClient, XiaohongshuConfig

from app.models.product import ProductSearchRequest, ProductSearchResponse


class ProductClient(XiaohongshuClient):
    """小红书商品API客户端"""
    
    def __init__(self, config: Optional[XiaohongshuConfig] = None, logger: Optional[logging.Logger] = None):
        """初始化商品客户端
        
        Args:
            config: API配置，如果不提供则使用默认配置
            logger: 日志记录器，如果不提供则使用默认记录器
        """
        super().__init__(config, logger)
    
    def search_products(self, page_no: int = 1, page_size: int = 20, sort_field: str = "create_time", 
                       order: str = "desc", card_type: int = 2, is_channel: bool = False) -> Dict[str, Any]:
        """搜索商品
        
        Args:
            page_no: 页码
            page_size: 每页数量
            sort_field: 排序字段
            order: 排序方式
            card_type: 卡片类型
            is_channel: 是否是频道
            
        Returns:
            搜索结果
        """
        path = "/api/edith/product/search_item_v2"
        
        # 构造请求数据
        data = {
            "page_no": page_no,
            "page_size": page_size,
            "search_order": {
                "sort_field": sort_field,
                "order": order
            },
            "search_filter": {
                "card_type": card_type,
                "is_channel": is_channel
            },
            "search_item_detail_option": {}
        }
        
        # 发送请求
        return self._make_request('POST', path, "", data=data)
    
    def get_product_detail(self, product_id: str) -> Dict[str, Any]:
        """获取商品详情
        
        Args:
            product_id: 商品ID
            
        Returns:
            商品详情
        """
        path = f"/api/edith/product/item/{product_id}"
        
        # 获取时间戳
        timestamp = str(int(time.time() * 1000))
        
        # 生成签名
        x_s = self.get_sign(timestamp, path, {})
        
        # 设置请求头
        self.session.headers.update({
            'x-s': x_s,
            'x-t': timestamp
        })
        
        # 发送请求
        return self._make_request('GET', path)
    
    def close(self):
        """关闭会话"""
        self.session.close() 