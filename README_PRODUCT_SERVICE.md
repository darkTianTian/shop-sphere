# 商品列表服务说明

## 概述

基于您提供的小红书商品列表API，我已经创建了一个完整的商品服务系统，包括数据模型、API客户端、业务服务和定时脚本。

## 新增模块结构

### 1. 数据模型层 (`app/models/product.py`)
- **`SearchOrder`**: 搜索排序配置
- **`SearchFilter`**: 搜索过滤条件  
- **`ProductSearchRequest`**: 商品搜索请求数据模型
- **`ProductInfo`**: 商品信息数据模型
- **`ProductSearchResponse`**: 商品搜索响应数据模型
- **`ProductSearchRequestBuilder`**: 商品搜索请求构建器

### 2. 服务层
- **`app/services/product_client.py`**: 商品API客户端
  - `ProductClient`: 封装HTTP请求逻辑
  - `ProductApiConfig`: API配置管理
  - 支持重试机制和错误处理

- **`app/services/product_service.py`**: 商品业务服务
  - `ProductService`: 封装商品搜索的业务逻辑
  - 提供商品信息格式化输出
  - 统一的错误处理和日志记录

### 3. 配置层 (`app/config/product_auth_config.py`)
- **`ProductAuthConfig`**: 商品API认证配置管理
  - 支持从环境变量加载配置
  - 提供默认配置用于测试

### 4. 定时脚本 (`app/scripts/fetch_products.py`)
- 每分钟执行的商品列表获取脚本
- 使用模块化的服务架构
- 详细的日志记录和错误处理

### 5. Supervisor配置 (`deploy/supervisor/fetch_products.conf`)
- 商品获取服务的进程管理配置
- 自动重启和日志管理

## API请求映射

原始API请求：
```python
url = "https://ark.xiaohongshu.com/api/edith/product/search_item_v2"
payload = {
  "page_no": 1,
  "page_size": 20,
  "search_order": {
    "sort_field": "create_time",
    "order": "desc"
  },
  "search_filter": {
    "card_type": 2,
    "is_channel": False
  },
  "search_item_detail_option": {}
}
headers = {
  'authorization': 'AT-68c517501635539317564573ibxkzxcsywqwxzaq',
  'x-s': 'OlqB1gFp1gclZjdBOjq6s6sp0YFbOgTCOYdUOgvKsgM3',
  'x-t': '1748021996358',
  'Cookie': 'acw_tc=0a42376617481667139967942e6237c41ee70482616d4b448efcd33c8702d7'
}
```

现在的模块化调用：
```python
from app.services.product_service import ProductService
from app.config.product_auth_config import ProductAuthConfig

# 初始化服务
service = ProductService()

# 设置认证
auth_config = ProductAuthConfig.get_default()
service.setup_auth(
    authorization=auth_config.authorization,
    x_s=auth_config.x_s,
    x_t=auth_config.x_t,
    cookie=auth_config.cookie
)

# 搜索商品
response = service.search_products()
service.print_search_summary(response)
```

## 使用方式

### 环境变量配置（推荐）
```bash
export PRODUCT_AUTHORIZATION="your_authorization_token"
export PRODUCT_X_S="your_x_s_value"
export PRODUCT_X_T="your_x_t_value"
export PRODUCT_COOKIE="your_cookie_value"
```

### 直接运行脚本
```bash
# 运行商品获取脚本
python app/scripts/fetch_products.py
```

### 在Docker中运行
脚本会自动通过supervisor管理，配置文件：`deploy/supervisor/fetch_products.conf`

## 功能特性

### 1. **智能日志输出**
脚本会详细记录：
- 任务执行时间
- API请求状态
- 商品搜索结果
- 商品详细信息
- 状态统计信息

### 2. **商品信息展示**
每次执行会显示：
```
=== 商品列表 (共 X 个商品) ===
商品 1:
  ID: product_id_1
  标题: 商品标题
  价格: 99.00
  状态: active
  创建时间: 2024-01-01 10:00:00
  更新时间: 2024-01-01 12:00:00
  ----------------------------------------
商品 2:
  ...
```

### 3. **统计信息**
```
📊 商品状态统计:
  active: 15 个
  inactive: 3 个
  pending: 2 个
```

### 4. **错误处理**
- 网络请求重试机制
- 详细的错误日志
- 优雅的异常处理

## 扩展示例

### 自定义搜索条件
```python
from app.models.product import ProductSearchRequestBuilder

builder = ProductSearchRequestBuilder()
request = (builder
          .set_page(1, 50)  # 获取50个商品
          .set_sort("update_time", "asc")  # 按更新时间升序
          .set_filter(card_type=1, is_channel=True)  # 自定义过滤
          .build())

response = service.search_products(request)
```

### 获取特定数量的商品
```python
# 获取最近的10个商品
recent_products = service.get_recent_products(limit=10)
service.print_products_info(recent_products)
```

### 添加其他定时任务
```python
# 在主脚本中添加每小时任务
scheduler.add_hourly_task(fetch_products_task, product_service, logger)

# 添加每日任务
scheduler.add_daily_task(daily_product_summary, product_service, logger, "09:00")
```

## 日志文件位置

- **标准输出**: `/var/log/supervisor/fetch_products_out.log`
- **错误输出**: `/var/log/supervisor/fetch_products_err.log`

## 与send_note服务的对比

| 特性 | send_note | fetch_products |
|------|-----------|----------------|
| 功能 | 发送小红书笔记 | 获取商品列表 |
| API端点 | `/web_api/sns/v2/note` | `/api/edith/product/search_item_v2` |
| 认证方式 | Cookie + x-s + x-t | Authorization + x-s + x-t + Cookie |
| 数据模型 | 笔记相关 | 商品相关 |
| 输出格式 | API响应 | 格式化商品信息 |
| 执行频率 | 每分钟 | 每分钟 |

## 测试验证

所有模块都通过了完整的单元测试：
- ✅ 数据模型导入和功能
- ✅ 请求构建器
- ✅ 认证配置管理
- ✅ 服务层功能
- ✅ 响应解析

## 总结

通过模块化设计，商品列表服务具有以下优势：
- **可维护性**: 清晰的模块分离
- **可扩展性**: 易于添加新功能
- **可配置性**: 支持环境变量配置
- **健壮性**: 完善的错误处理
- **可观测性**: 详细的日志记录

现在您可以通过运行 `python app/scripts/fetch_products.py` 来启动商品列表获取服务，它会每分钟自动调用API并打印出商品信息。 