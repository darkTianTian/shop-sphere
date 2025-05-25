import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import pytz

from app.services.product_client import ProductClient, ProductApiConfig
from app.models.product import ProductSearchRequestBuilder, ProductSearchRequest, ProductSearchResponse, ProductInfo


class ProductService:
    """商品服务"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.client = ProductClient(logger=self.logger)
        
    def setup_auth(self, authorization: str, x_s: str, x_t: str, cookie: str):
        """设置认证信息"""
        self.client.set_auth_headers(authorization, x_s, x_t, cookie)
        
    def create_default_search_request(self, page_no: int = 1, page_size: int = 20) -> ProductSearchRequest:
        """创建默认的搜索请求"""
        builder = ProductSearchRequestBuilder()
        return (builder
                .set_page(page_no, page_size)
                .set_sort("create_time", "desc")
                .set_filter(card_type=2, is_channel=False)
                .set_detail_option({})
                .build())
    
    def search_products(self, request: Optional[ProductSearchRequest] = None) -> ProductSearchResponse:
        """
        搜索商品列表
        
        Args:
            request: 搜索请求，如果为None则使用默认请求
            
        Returns:
            商品搜索响应
        """
        if request is None:
            request = self.create_default_search_request()
            
        try:
            self.logger.info("开始搜索商品列表")
            response = self.client.search_products(request)
            
            if response.success:
                self.logger.info(f"商品搜索成功，找到 {len(response.products)} 个商品")
            else:
                self.logger.warning(f"商品搜索失败: {response.message}")
                
            return response
        except Exception as e:
            self.logger.error(f"搜索商品失败: {str(e)}")
            return ProductSearchResponse(
                success=False,
                message=f"搜索异常: {str(e)}",
                code=-1
            )
    
    def get_recent_products(self, limit: int = 10) -> List[ProductInfo]:
        """
        获取最近的商品列表
        
        Args:
            limit: 限制返回的商品数量
            
        Returns:
            商品信息列表
        """
        request = self.create_default_search_request(page_size=limit)
        response = self.search_products(request)
        
        if response.success:
            return response.products[:limit]
        else:
            self.logger.error(f"获取最近商品失败: {response.message}")
            return []
    
    def print_products_info(self, products: List[ProductInfo]):
        """
        打印商品信息
        
        Args:
            products: 商品信息列表
        """
        if not products:
            self.logger.info("没有找到商品信息")
            return
            
        self.logger.info(f"=== 商品列表 (共 {len(products)} 个商品) ===")
        
        for i, product in enumerate(products, 1):
            info_lines = [
                f"商品 {i}:",
                f"  ID: {product.id or 'N/A'}",
                f"  标题: {product.title or 'N/A'}",
                f"  价格: {product.price or 'N/A'}",
                f"  状态: {product.status or 'N/A'}",
                f"  创建时间: {product.create_time or 'N/A'}",
                f"  更新时间: {product.update_time or 'N/A'}"
            ]
            
            for line in info_lines:
                self.logger.info(line)
            
            if i < len(products):  # 不是最后一个商品时添加分隔线
                self.logger.info("  " + "-" * 40)
    
    def print_search_summary(self, response: ProductSearchResponse):
        """
        打印搜索结果摘要
        
        Args:
            response: 搜索响应对象
        """
        if response.success:
            total_count = len(response.products)
            self.logger.info(f"✅ 商品搜索成功")
            self.logger.info(f"📦 找到商品数量: {total_count}")
            
            if response.data:
                # 如果API返回了总数等额外信息
                if 'total' in response.data:
                    self.logger.info(f"📊 总商品数: {response.data['total']}")
                if 'page_info' in response.data:
                    page_info = response.data['page_info']
                    self.logger.info(f"📄 分页信息: 第{page_info.get('page_no', 'N/A')}页，每页{page_info.get('page_size', 'N/A')}条")
            
            # 打印商品详细信息
            self.print_products_info(response.products)
        else:
            self.logger.error(f"❌ 商品搜索失败")
            self.logger.error(f"错误代码: {response.code}")
            self.logger.error(f"错误信息: {response.message}")
    
    def close(self):
        """关闭服务"""
        self.client.close() 