#!/usr/bin/env python3
import sys
import os
from datetime import datetime
import pytz
from sqlmodel import Session, select
import traceback

# 设置基本的错误日志
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
base_logger = logging.getLogger('fetch_products')

# 获取环境信息
SERVER_ENV = os.environ.get('SERVER_ENVIRONMENT', 'LOCAL')
base_logger.info(f"Starting fetch_products in {SERVER_ENV} environment")
base_logger.info(f"Current PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
base_logger.info(f"Current working directory: {os.getcwd()}")

# 引入封装的logger
try:
    from app.utils.logger import setup_logger
    from app.utils.scheduler import TaskScheduler
    from app.services.xiaohongshu.product_client import ProductClient
    from app.config.auth_config import AuthConfig
    from app.models.product import Product
    from app.internal.db import engine
except ImportError as e:
    error_msg = f"导入模块失败: {str(e)}\n{traceback.format_exc()}"
    base_logger.error(error_msg)
    sys.exit(1)

# 通过settings.load_settings()动态加载配置
try:
    from app.settings import load_settings
    settings = load_settings()
    base_logger.info("Successfully loaded settings")
except Exception as e:
    error_msg = f"加载设置失败: {str(e)}\n{traceback.format_exc()}"
    base_logger.error(error_msg)
    sys.exit(1)

def save_result(result: dict, logger):
    """保存结果到数据库
    
    Args:
        result: API响应结果
        logger: 日志记录器
    """
    try:
        if not result.get('success') or 'data' not in result or 'items' not in result['data']:
            logger.warning("无效的API响应结果")
            return
            
        items = result['data']['items']
        products_to_save = []
        
        # 将API响应数据转换为Product模型实例
        for item in items:
            try:
                product = Product.from_api_response(item)
                products_to_save.append(product)
            except Exception as e:
                logger.error(f"处理商品数据时出错: {str(e)}, 商品数据: {item}")
                continue
        
        # 保存到数据库
        with Session(engine) as session:
            for product in products_to_save:
                # 检查是否已存在
                stmt = select(Product).where(Product.item_id == product.item_id)
                existing_product = session.exec(stmt).first()
                
                if existing_product:
                    # 更新现有记录
                    existing_product.item_name = product.item_name
                    existing_product.desc = product.desc
                    existing_product.min_price = product.min_price
                    existing_product.max_price = product.max_price
                    existing_product.update_time = datetime.now()
                    logger.info(f"更新商品: {product.item_id}")
                else:
                    # 添加新记录
                    session.add(product)
                    logger.info(f"新增商品: {product.item_id}")
            
            session.commit()
            
        logger.info(f"成功保存 {len(products_to_save)} 个商品到数据库")
        
    except Exception as e:
        error_msg = f"保存结果到数据库失败: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)

def fetch_products_task(product_service: ProductClient, logger):
    """获取商品列表任务"""
    try:
        current_time = datetime.now(pytz.timezone(settings.TIMEZONE)).strftime("%Y-%m-%d %H:%M:%S")
        message = f"[{SERVER_ENV}] 开始获取商品列表任务 at {current_time}"
        logger.info(message)
        
        # 搜索商品列表
        response = product_service.search_products(
            page_no=1,
            page_size=20,
            sort_field="create_time",
            order="desc",
            card_type=2,
            is_channel=False
        )
        
        # 打印结果摘要
        logger.info("\n=== 搜索结果 ===")
        logger.info(f"状态: {'成功' if response.get('success') else '失败'}")
        logger.info(f"代码: {response.get('code')}")
        logger.info(f"消息: {response.get('msg')}")
        
        # 如果成功，额外打印一些统计信息
        if response.get('success') and 'data' in response and 'items' in response['data']:
            items = response['data']['items']
            logger.info("=" * 60)
            logger.info(f"🎉 本次任务完成，成功获取 {len(items)} 个商品信息")
            
            # 统计不同状态的商品数量
            status_count = {}
            for item in items:
                status = item.get('status', 'unknown')
                status_count[status] = status_count.get(status, 0) + 1
            
            if status_count:
                logger.info("📊 商品状态统计:")
                for status, count in status_count.items():
                    logger.info(f"  {status}: {count} 个")
            
            # 保存结果到数据库
            save_result(response, logger)
        
        logger.info("=" * 60)
        
    except Exception as e:
        error_msg = f"获取商品列表任务失败: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)

def main():
    base_logger.info("Starting main function")
    
    # 使用supervisor配置的日志路径
    log_file = '/var/log/supervisor/fetch_products_out.log'
    
    # 使用封装的logger
    try:
        logger = setup_logger(
            name=f'fetch_products_{SERVER_ENV.lower()}',
            log_file=log_file,
            level=20,  # logging.INFO
            log_to_stderr=False  # 修改这里，因为supervisor已经处理了日志重定向
        )
        logger.info("Logger setup completed")
    except Exception as e:
        error_msg = f"设置日志失败: {str(e)}\n{traceback.format_exc()}"
        base_logger.error(error_msg)
        sys.exit(1)
        
    logger.info(f"Product fetch service started in {SERVER_ENV} environment")
    
    # 初始化商品服务
    product_service = ProductClient(logger=logger)
    
    # 设置认证信息
    try:
        # 获取认证配置
        auth_config = AuthConfig.get_default()
        product_service.set_auth(auth_config)
        logger.info("商品API认证配置设置完成")
        
    except Exception as e:
        error_msg = f"设置商品API认证配置失败: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        sys.exit(1)
    
    # 创建任务调度器
    try:
        scheduler = TaskScheduler(
            timezone=settings.TIMEZONE,
            logger=logger
        )
        
        # 添加每分钟执行的任务
        scheduler.add_hourly_task(fetch_products_task, 0, product_service, logger)
        
        logger.info("已添加每小时获取商品列表的定时任务")
        
        # 启动调度器
        scheduler.start()
        
    except KeyboardInterrupt:
        logger.info("Product fetch service stopped by user")
        sys.exit(0)
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        error_msg = f"Main function failed: {str(e)}\n{traceback.format_exc()}"
        base_logger.error(error_msg)
        sys.exit(1) 