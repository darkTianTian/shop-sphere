from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import json
from datetime import datetime
from sqlmodel import Field, SQLModel


@dataclass
class SearchOrder:
    """搜索排序配置"""
    sort_field: str = "create_time"
    order: str = "desc"


@dataclass
class SearchFilter:
    """搜索过滤条件"""
    card_type: int = 2
    is_channel: bool = False


@dataclass
class ProductSearchRequest:
    """商品搜索请求数据模型"""
    page_no: int = 1
    page_size: int = 20
    search_order: SearchOrder = None
    search_filter: SearchFilter = None
    search_item_detail_option: Dict[str, Any] = None

    def __post_init__(self):
        if self.search_order is None:
            self.search_order = SearchOrder()
        if self.search_filter is None:
            self.search_filter = SearchFilter()
        if self.search_item_detail_option is None:
            self.search_item_detail_option = {}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "page_no": self.page_no,
            "page_size": self.page_size,
            "search_order": {
                "sort_field": self.search_order.sort_field,
                "order": self.search_order.order
            },
            "search_filter": {
                "card_type": self.search_filter.card_type,
                "is_channel": self.search_filter.is_channel
            },
            "search_item_detail_option": self.search_item_detail_option
        }

    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False)


@dataclass
class ProductInfo:
    """商品信息数据模型"""
    id: Optional[str] = None
    title: Optional[str] = None
    price: Optional[str] = None
    status: Optional[str] = None
    create_time: Optional[str] = None
    update_time: Optional[str] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProductInfo':
        """从字典创建商品信息"""
        return cls(
            id=data.get('id'),
            title=data.get('title'),
            price=data.get('price'),
            status=data.get('status'),
            create_time=data.get('create_time'),
            update_time=data.get('update_time')
        )


@dataclass
class ProductSearchResponse:
    """商品搜索响应数据模型"""
    success: bool
    code: Optional[int] = None
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    products: List[ProductInfo] = None

    def __post_init__(self):
        if self.products is None:
            self.products = []

    @classmethod
    def from_dict(cls, response_data: Dict[str, Any]) -> 'ProductSearchResponse':
        """从API响应创建对象"""
        success = response_data.get('success', False)
        code = response_data.get('code')
        message = response_data.get('message', '')
        data = response_data.get('data', {})
        
        products = []
        if data and 'items' in data:
            for item in data['items']:
                products.append(ProductInfo.from_dict(item))
        
        return cls(
            success=success,
            code=code,
            message=message,
            data=data,
            products=products
        )


class ProductSearchRequestBuilder:
    """商品搜索请求构建器"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """重置构建器"""
        self._request = ProductSearchRequest()
        return self
    
    def set_page(self, page_no: int, page_size: int = 20):
        """设置分页参数"""
        self._request.page_no = page_no
        self._request.page_size = page_size
        return self
    
    def set_sort(self, sort_field: str = "create_time", order: str = "desc"):
        """设置排序参数"""
        self._request.search_order = SearchOrder(sort_field=sort_field, order=order)
        return self
    
    def set_filter(self, card_type: int = 2, is_channel: bool = False):
        """设置过滤条件"""
        self._request.search_filter = SearchFilter(card_type=card_type, is_channel=is_channel)
        return self
    
    def set_detail_option(self, options: Dict[str, Any]):
        """设置详情选项"""
        self._request.search_item_detail_option = options
        return self
    
    def build(self) -> ProductSearchRequest:
        """构建请求对象"""
        return self._request 


class Product(SQLModel, table=True):
    """商品模型"""
    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: str = Field(index=True)
    title: str
    desc: Optional[str] = None
    price: Optional[float] = None
    status: Optional[str] = None
    create_time: datetime = Field(default_factory=datetime.now)
    update_time: datetime = Field(default_factory=datetime.now)
    
    @classmethod
    def from_api_response(cls, item: dict) -> "Product":
        """从API响应创建商品实例"""
        return cls(
            product_id=str(item.get('id', '')),
            title=item.get('title', ''),
            desc=item.get('desc', ''),
            price=float(item.get('price', 0)) if item.get('price') else None,
            status=item.get('status', 'unknown'),
        ) 