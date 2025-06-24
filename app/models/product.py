from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import json
import time
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship, Enum as SQLEnum
import sqlalchemy as sa
from enum import Enum, auto
from app.models.base import BaseModel

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


class ProductStatus(str, Enum):
    """商品状态枚举"""
    ON_SHELF = "on_shelf"
    OFF_SHELF = "off_shelf"
    DELETED = "deleted"


class Product(BaseModel, table=True):
    """商品模型"""
    item_id: str = Field(index=True)
    item_name: str = Field()
    desc: Optional[str] = Field(default="")
    status: ProductStatus = Field(default=ProductStatus.ON_SHELF, sa_column=sa.Column(sa.Enum(ProductStatus)))
    buyable: bool = Field(default=True)
    item_create_time: int = Field(default=0, sa_type=sa.BigInteger, index=True)
    item_update_time: int = Field(default=0, sa_type=sa.BigInteger, index=True)
    min_price: int = Field(default=0)
    max_price: int = Field(default=0)
    product_note_num: int = Field(default=0)
    
    # on_shelf_sku_count: int = Field(default=0)
    # off_shelf_sku_count: int = Field(default=0)
    # is_channel: bool = Field(default=False)
    # category_check_status: int = Field(default=0)
    seller_id: str = Field(default="")
    delivery_mode: int = Field(default=0)
    # allowance_plan: bool = Field(default=False)
    # is_free_return: bool = Field(default=False)
    xsec_token: str = Field(default="")
    # sale_qty_info: dict = Field(default={})
    # order_note_num: int = Field(default=0)
    deleted: bool = Field(default=False)
    # check_status: int = Field(default=0)
    sku_count: int = Field(default=0)
    category_id: str = Field(default="", index=True)
    on_sale_sku_count: int = Field(default=0)
    main_spec_id: str = Field(default="")
    on_shelf_time: int = Field(default=0, sa_type=sa.BigInteger)
    first_sku_id: str = Field(default="")
    shipping_template_id: str = Field(default="")
    # image_descriptions: List[dict] = Field(default=[])
    # item_audit_status: int = Field(default=0)
    # union_type: int = Field(default=0)
    total_stock: int = Field(default=0)
    # expected_purchase_time: int = Field(default=0, sa_type=sa.BigInteger)
    # use_playback: int = Field(default=0)
    # sold_out_sku_count: int = Field(default=0)
    # is_o2_o: bool = Field(default=False)
    brand_audit_result: int = Field(default=0)
    item_name_with_brand_name: str = Field(default="")
    # is_item_attend_promotion: bool = Field(default=False)
    # is_genuine_guarantee: bool = Field(default=False)
    # item_audit_time: int = Field(default=0, sa_type=sa.BigInteger)
    # auto_off_shelf_time: int = Field(default=0, sa_type=sa.BigInteger)
    # need_qic: bool = Field(default=False)
    # category_audit_result: int = Field(default=0)
    # stock_type: int = Field(default=0)
    # min_membership_price: int = Field(default=0)
    # o2o_show_shop_address: bool = Field(default=False)
    # contains_multi_package: bool = Field(default=False)
    # contains_gift: bool = Field(default=False)
    # is_boutique: bool = Field(default=False)
    # faqs: List[dict] = Field(default=[])
    # is_nft: bool = Field(default=False)
    # item_auditing_time: int = Field(default=0, sa_type=sa.BigInteger)
    platform: str = Field(default="")
    images: str = Field(default='{}', sa_type=sa.JSON)
    
    @classmethod
    def from_api_response(cls, item: dict) -> "Product":
        """从API响应创建商品实例"""
        """{
                "description": "",
                "buyable": true,
                "item_punish_result": 1,
                "first_buyable_sku_id": "68307e5ab6240c0015112434",
                "item_freeze": false,
                "update_time": 1748009341000,
                "diagnosisInfo": {
                    "status": 2,
                    "diagnosisIssues": [
                        {
                            "key": "withoutSpecImage",
                            "desc": "缺少规格大图"
                        }
                    ],
                    "hint": "影响: 流量分发、商品详情转化"
                },
                "is_auto_off_shelf": false,
                "min_price": 900,
                "is_education_pricing": false,
                "category_check_time": 1748009338091,
                "product_note_num": 0,
                "images": [
                    {
                        "material_id": "6268386b-0541-4579-b6f4-456e3b4284ee",
                        "path": "material_space/6268386b-0541-4579-b6f4-456e3b4284ee",
                        "extension": ".jpeg",
                        "width": 800,
                        "height": 800,
                        "link": "https://qimg.xiaohongshu.com/material_space/6268386b-0541-4579-b6f4-456e3b4284ee",
                        "size": 0
                    },
                    {
                        "material_id": "5313ba44-efcc-4212-b192-f13c8cc19dde",
                        "path": "material_space/5313ba44-efcc-4212-b192-f13c8cc19dde",
                        "extension": ".jpeg",
                        "width": 800,
                        "height": 800,
                        "link": "https://qimg.xiaohongshu.com/material_space/5313ba44-efcc-4212-b192-f13c8cc19dde",
                        "size": 0
                    },
                    {
                        "height": 800,
                        "link": "https://qimg.xiaohongshu.com/material_space/f9f8562d-ae78-4f7b-b5fd-1f08da2b4575",
                        "size": 0,
                        "material_id": "f9f8562d-ae78-4f7b-b5fd-1f08da2b4575",
                        "path": "material_space/f9f8562d-ae78-4f7b-b5fd-1f08da2b4575",
                        "extension": ".jpeg",
                        "width": 800
                    },
                    {
                        "size": 0,
                        "material_id": "9253dbd5-fea7-41a3-ad40-d25ea8ee0fcc",
                        "path": "material_space/9253dbd5-fea7-41a3-ad40-d25ea8ee0fcc",
                        "extension": ".jpeg",
                        "width": 800,
                        "height": 800,
                        "link": "https://qimg.xiaohongshu.com/material_space/9253dbd5-fea7-41a3-ad40-d25ea8ee0fcc"
                    },
                    {
                        "width": 800,
                        "height": 800,
                        "link": "https://qimg.xiaohongshu.com/material_space/42325a3c-1034-4c4b-8874-fe2e4f99adad",
                        "size": 0,
                        "material_id": "42325a3c-1034-4c4b-8874-fe2e4f99adad",
                        "path": "material_space/42325a3c-1034-4c4b-8874-fe2e4f99adad",
                        "extension": ".jpeg"
                    }
                ],
                "item_name": "宠物梳子猫咪梳毛神器宠物开结梳浮毛梳狗狗按摩除毛梳宠物用品",
                "on_shelf_sku_count": 8,
                "is_channel": false,
                "category_check_status": 1,
                "is_item_attend_activity": false,
                "cross_border_status": true,
                "seller_id": "67504cbd8e2c970015e02516",
                "delivery_mode": 0,
                "allowance_plan": false,
                "create_time": 1748008536000,
                "shipping_gross_weight": 1000,
                "off_shelf_sku_count": 0,
                "is_general_settings": {
                    "shippingFeeMode": false,
                    "imagesDesc": true,
                    "logisticsPlanId": false,
                    "imagesDescV2": false,
                    "deliveryTime": false,
                    "imageBindSpu": true,
                    "whcode": false
                },
                "attributes": [],
                "main_spec_enable": 0,
                "config_size_table_info": [],
                "categories": [
                    {
                        "id": "65f994ca3e946300016aeef1",
                        "name": "宠物/宠物食品及用品",
                        "ename": "",
                        "level": 1,
                        "parent_id": "",
                        "is_leaf": false,
                        "category_type": 1
                    },
                    {
                        "name": "猫/狗美容护理工具",
                        "ename": "",
                        "level": 2,
                        "parent_id": "65f994ca3e946300016aeef1",
                        "is_leaf": false,
                        "category_type": 1,
                        "id": "65f994ce3e946300016aef5d"
                    },
                    {
                        "parent_id": "65f994ce3e946300016aef5d",
                        "is_leaf": true,
                        "category_type": 1,
                        "id": "65f994ce3e946300016aef63",
                        "name": "猫狗梳子/排梳",
                        "ename": "",
                        "level": 3
                    }
                ],
                "max_membership_price": 0,
                "is_item_attend_promotion": false,
                "is_free_return": true,
                "max_price": 1800,
                "variant_ids": [
                    "5a60c42f69bd891ed8939bc2",
                    "60404e0de85df80001991224"
                ],
                "size_table_type": 1,
                "xsec_token": "ABkUpm3nkTAuHqHpC6EckIynfr9dRbr1WBpHZ4k7_siK4=",
                "sale_qty_info": {
                    "acc_sale_qty": 0,
                    "sale_qty30": 0,
                    "sale_qty_update_time": 1749686400470
                },
                "enable_multi_warehouse": false,
                "free_return": 1,
                "order_note_num": 0,
                "deleted": false,
                "is_boutique": false,
                "faqs": [],
                "is_nft": false,
                "item_auditing_time": 1748008549576,
                "auto_off_shelf_time": 0,
                "need_qic": false,
                "category_audit_result": 1,
                "check_status": 1,
                "stock_type": 1,
                "min_membership_price": 0,
                "o2o_show_shop_address": false,
                "sku_count": 8,
                "is_genuine_guarantee": false,
                "item_audit_time": 1748008668151,
                "contains_multi_package": false,
                "category_id": "65f994ce3e946300016aef63",
                "contains_gift": false,
                "on_sale_sku_count": 8,
                "main_spec_id": "60404e0de85df80001991224",
                "size_table_params": [],
                "on_shelf_time": 1748008670000,
                "first_sku_id": "68307e5ab6240c0015112434",
                "item_id": "68307e58e0db0d0015a4467b",
                "shipping_template_id": "675051beaa3e340001000b56",
                "image_descriptions": [
                    {
                        "extension": ".jpeg",
                        "width": 790,
                        "height": 1000,
                        "link": "https://qimg.xiaohongshu.com/material_space/83a4cf81-a8e4-41be-864c-fd5772518869",
                        "size": 0,
                        "material_id": "83a4cf81-a8e4-41be-864c-fd5772518869",
                        "path": "material_space/83a4cf81-a8e4-41be-864c-fd5772518869"
                    },
                    {
                        "link": "https://qimg.xiaohongshu.com/material_space/aa4ae7fa-7870-487c-8239-7ea7391213f7",
                        "size": 0,
                        "material_id": "aa4ae7fa-7870-487c-8239-7ea7391213f7",
                        "path": "material_space/aa4ae7fa-7870-487c-8239-7ea7391213f7",
                        "extension": ".jpeg",
                        "width": 790,
                        "height": 1000
                    },
                    {
                        "size": 0,
                        "material_id": "0af98232-cfee-4557-81fb-e8961edbfeaf",
                        "path": "material_space/0af98232-cfee-4557-81fb-e8961edbfeaf",
                        "extension": ".jpeg",
                        "width": 790,
                        "height": 1000,
                        "link": "https://qimg.xiaohongshu.com/material_space/0af98232-cfee-4557-81fb-e8961edbfeaf"
                    },
                    {
                        "path": "material_space/28ebc36c-a224-4a40-90a3-66edb194678c",
                        "extension": ".jpeg",
                        "width": 790,
                        "height": 1000,
                        "link": "https://qimg.xiaohongshu.com/material_space/28ebc36c-a224-4a40-90a3-66edb194678c",
                        "size": 0,
                        "material_id": "28ebc36c-a224-4a40-90a3-66edb194678c"
                    },
                    {
                        "height": 1000,
                        "link": "https://qimg.xiaohongshu.com/material_space/e9d5d649-60d5-4535-b57e-32ab8a2f88fa",
                        "size": 0,
                        "material_id": "e9d5d649-60d5-4535-b57e-32ab8a2f88fa",
                        "path": "material_space/e9d5d649-60d5-4535-b57e-32ab8a2f88fa",
                        "extension": ".jpeg",
                        "width": 790
                    },
                    {
                        "width": 790,
                        "height": 1000,
                        "link": "https://qimg.xiaohongshu.com/material_space/b878b9dd-da31-4dc4-b629-f67bce267154",
                        "size": 0,
                        "material_id": "b878b9dd-da31-4dc4-b629-f67bce267154",
                        "path": "material_space/b878b9dd-da31-4dc4-b629-f67bce267154",
                        "extension": ".jpeg"
                    },
                    {
                        "size": 0,
                        "material_id": "e3d7e565-1194-4f12-9efb-75c7059cc74e",
                        "path": "material_space/e3d7e565-1194-4f12-9efb-75c7059cc74e",
                        "extension": ".jpeg",
                        "width": 790,
                        "height": 1000,
                        "link": "https://qimg.xiaohongshu.com/material_space/e3d7e565-1194-4f12-9efb-75c7059cc74e"
                    },
                    {
                        "path": "material_space/7ed0ba28-39ff-4a34-9972-9d7a26ec55f7",
                        "extension": ".jpeg",
                        "width": 790,
                        "height": 1250,
                        "link": "https://qimg.xiaohongshu.com/material_space/7ed0ba28-39ff-4a34-9972-9d7a26ec55f7",
                        "size": 0,
                        "material_id": "7ed0ba28-39ff-4a34-9972-9d7a26ec55f7"
                    }
                ],
                "item_audit_status": 2,
                "union_type": 0,
                "total_stock": 65589,
                "expected_purchase_time": 0,
                "use_playback": 0,
                "sold_out_sku_count": 0,
                "is_o2_o": false,
                "brand_audit_result": 1,
                "item_name_with_brand_name": "宠物梳子猫咪梳毛神器宠物开结梳浮毛梳狗狗按摩除毛梳宠物用品"
            }"""
        return cls(
            item_id=item.get('item_id', ''),
            item_name=item.get('item_name', ''),
            desc=item.get('description', ''),
            status=item.get('status', 0),
            buyable=item.get('buyable', True),
            item_create_time=item.get('create_time', 0),
            item_update_time=item.get('update_time', 0),
            min_price=item.get('min_price', 0),
            max_price=item.get('max_price', 0),
            images=item.get('images', []),
            categories=item.get('categories', []),
            # is_auto_off_shelf=item.get('is_auto_off_shelf', False),
            # is_education_pricing=item.get('is_education_pricing', False),
            product_note_num=item.get('product_note_num', 0),
            # on_shelf_sku_count=item.get('on_shelf_sku_count', 0),
            # is_channel=item.get('is_channel', False),
            # category_check_status=item.get('category_check_status', 0),
            # category_check_time=item.get('category_check_time', 0),
            seller_id=item.get('seller_id', ''),
            delivery_mode=item.get('delivery_mode', 0),
            # allowance_plan=item.get('allowance_plan', False),
            # is_free_return=item.get('is_free_return', False),
            xsec_token=item.get('xsec_token', ''),
            # sale_qty_info=item.get('sale_qty_info', {}),
            # order_note_num=item.get('order_note_num', 0), 
            deleted=item.get('deleted', False),
            # check_status=item.get('check_status', 0),
            sku_count=item.get('sku_count', 0),
            category_id=item.get('category_id', ''),
            on_sale_sku_count=item.get('on_sale_sku_count', 0),
            main_spec_id=item.get('main_spec_id', ''),
            on_shelf_time=item.get('on_shelf_time', 0),
            first_sku_id=item.get('first_sku_id', ''),
            shipping_template_id=item.get('shipping_template_id', ''),
            image_descriptions=item.get('image_descriptions', []),
            # item_audit_status=item.get('item_audit_status', 0),
            # union_type=item.get('union_type', 0),
            total_stock=item.get('total_stock', 0),
            # expected_purchase_time=item.get('expected_purchase_time', 0),
            # use_playback=item.get('use_playback', 0),
            # sold_out_sku_count=item.get('sold_out_sku_count', 0),
            # is_o2_o=item.get('is_o2_o', False),
            brand_audit_result=item.get('brand_audit_result', 0),
            item_name_with_brand_name=item.get('item_name_with_brand_name', ''),
            # is_item_attend_promotion=item.get('is_item_attend_promotion', False),
            # is_genuine_guarantee=item.get('is_genuine_guarantee', False),
            # item_audit_time=item.get('item_audit_time', 0),
            # auto_off_shelf_time=item.get('auto_off_shelf_time', 0),
            # need_qic=item.get('need_qic', False),
            # category_audit_result=item.get('category_audit_result', 0),
            # stock_type=item.get('stock_type', 0),
            # min_membership_price=item.get('min_membership_price', 0),
            # o2o_show_shop_address=item.get('o2o_show_shop_address', False),
            # contains_multi_package=item.get('contains_multi_package', False),
            # contains_gift=item.get('contains_gift', False),
            # is_boutique=item.get('is_boutique', False),
            # faqs=item.get('faqs', []),
            # is_nft=item.get('is_nft', False),
            # item_auditing_time=item.get('item_auditing_time', 0),
            create_time=datetime.fromtimestamp(item.get('create_time', int(time.time() * 1000)) // 1000),  # Convert milliseconds to seconds
            update_time=datetime.fromtimestamp(item.get('update_time', int(time.time() * 1000)) // 1000),  # Convert milliseconds to seconds
        ) 
    

class ArticleStatus(str, Enum):
    """文章状态枚举"""
    DRAFT = "draft"      # 草稿
    PENDING_REVIEW = "pending_review"    # 待审核
    REJECTED = "rejected"   # 已拒绝
    PENDING_PUBLISH = "pending_publish"    # 待发布
    PUBLISHED = "published"  # 已发布
    PUBLISH_FAILED = "publish_failed"  # 发布失败

    @classmethod
    def get_description(cls, status: str) -> str:
        """获取状态描述"""
        try:
            return cls(status).name
        except ValueError:
            return "未知状态"


class ProductArticle(BaseModel, table=True):
    __tablename__ = "product_article"
    """商品文章模型"""
    item_id: str = Field(index=True, description="商品ID")
    sku_id: str = Field(index=True, description="SKU ID")
    title: str = Field(description="文章标题")
    content: str = Field(description="文章内容", sa_type=sa.String(length=4096))
    tag_ids: str = Field(description="话题标签ID列表, 逗号分隔", sa_type=sa.String(length=1024))
    tags: Optional[str] = Field(default="", description="生成文章时的标签，逗号分隔", sa_type=sa.String(length=256))
    owner_id: str = Field(description="文章作者ID")
    author_name: str = Field(description="文章作者名称")
    status: ArticleStatus = Field(
        sa_column=sa.Column(sa.Enum(ArticleStatus)),
        default=ArticleStatus.DRAFT,
        description="状态"
    )
    pre_publish_time: int = Field(default=0, sa_type=sa.BigInteger, description="预发布时间")
    publish_time: int = Field(default=0, sa_type=sa.BigInteger, description="发布时间")


class Tag(SQLModel, table=True):
    """标签模型"""
    id: str = Field(primary_key=True)
    name: str = Field(description="标签名称")
    link: str = Field(description="标签链接")
    type: str = Field(description="标签类型")
    platform: str = Field(description="平台")
    create_at: int = Field(default_factory=lambda: int(time.time()*1000), sa_type=sa.BigInteger)
    update_at: int = Field(default_factory=lambda: int(time.time()*1000), sa_type=sa.BigInteger)


class ArticleVideoMapping(BaseModel, table=True):
    """文章视频关联表"""
    __tablename__ = "article_video_mapping"
    
    article_id: int = Field(foreign_key="product_article.id", index=True, description="文章ID")
    video_id: int = Field(foreign_key="video.id", index=True, description="视频ID")
    status: str = Field(default="published", description="关联状态", sa_type=sa.String(length=32))
    publish_time: int = Field(default=0, sa_type=sa.BigInteger, description="发布时间")