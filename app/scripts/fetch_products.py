#!/usr/bin/env python3
import sys
import os
from datetime import datetime
import pytz
import random
from sqlmodel import Session, select
import traceback
import time
import logging

from app.models.product import ProductStatus
from app.utils.logger import setup_logger
from app.utils.scheduler import TaskScheduler
from app.services.xiaohongshu.product_client import ProductClient
from app.config.auth_config import AuthConfig
from app.models.product import Product
from app.internal.db import engine

# 获取环境信息
SERVER_ENV = os.environ.get('SERVER_ENVIRONMENT', 'LOCAL')

# 设置日志记录器
try:
    logger = setup_logger(
        name=f'fetch_products_{SERVER_ENV.lower()}',
        log_file=None,  # 不使用文件输出，让supervisor处理
        level=logging.INFO
    )
except Exception as e:
    error_msg = f"设置日志失败: {str(e)}\n{traceback.format_exc()}"
    print(error_msg, file=sys.stderr)  # 直接打印到stderr
    sys.exit(1)

# 通过settings.load_settings()动态加载配置
try:
    from app.settings import load_settings
    settings = load_settings()
    logger.info("Successfully loaded settings")
except Exception as e:
    error_msg = f"加载设置失败: {str(e)}\n{traceback.format_exc()}"
    logger.error(error_msg)
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
        add_cnt = 0
        update_cnt = 0
        
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
                    existing_product.buyable = product.buyable
                    existing_product.images = product.images
                    existing_product.deleted = product.deleted
                    existing_product.total_stock = product.total_stock
                    existing_product.first_sku_id = product.first_sku_id
                    logger.info(f"更新商品: {product.item_id}")
                    if not product.buyable:
                        existing_product.status = ProductStatus.UNMANAGED
                    # else:
                    #     existing_product.status = ProductStatus.MANAGED
                    update_cnt += 1
                elif product.buyable:
                    # 添加新记录
                    # product.status = ProductStatus.MANAGED
                    session.add(product)
                    logger.info(f"新增商品: {product.item_id}")
                    add_cnt += 1
            session.commit()
            
        logger.info(f"成功保存 {len(products_to_save)} 个商品到数据库，新增 {add_cnt} 个，更新 {update_cnt} 个")
        
    except Exception as e:
        error_msg = f"保存结果到数据库失败: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)

def fetch_products_task(product_service: ProductClient, logger):
    """获取商品列表任务"""
    try:
        current_time = datetime.now(pytz.timezone(settings.TIMEZONE)).strftime("%Y-%m-%d %H:%M:%S")
        message = f"[{SERVER_ENV}] 开始获取商品列表任务 at {current_time}"
        logger.info(message)
        
        page = 1
        page_size = 20
        total_products = []
        total_pages = None
        max_failures = 5  # 允许的连续失败次数
        consecutive_failures = 0
        
        while True:
            # 搜索商品列表
            response = product_service.search_products(
                page_no=page,
                page_size=page_size,
                sort_field="create_time",
                order="desc",
                card_type=1,
                is_channel=False
            )
            
            # 检查响应是否成功
            if not response.get('success') or 'data' not in response:
                logger.error(f"第 {page} 页请求失败")
                consecutive_failures += 1
                if consecutive_failures >= max_failures:
                    logger.error(f"连续 {consecutive_failures} 页请求失败，终止任务")
                    break
                # 继续下一页，或也可以重试当前页；这里选择跳过当前页
                page += 1
                # 随机短暂休眠，避免瞬时连续请求
                time.sleep(random.randint(1,3))
                continue
            
            # 成功获取后重置失败计数
            consecutive_failures = 0
            
            # 获取当前页的商品
            items = response['data'].get('items', [])
            if not items:
                break
                
            # 第一页时获取总数，计算总页数
            if page == 1:
                total = response['data'].get('total', 0)
                total_pages = (total + page_size - 1) // page_size
                logger.info(f"商品总数: {total}, 总页数: {total_pages}")
            
            # 收集商品数据
            total_products.extend(items)
            logger.info(f"已获取第 {page} 页数据，当前共 {len(total_products)} 个商品")
            
            # 判断是否还有下一页
            if not total_pages or page >= total_pages:
                break
                
            page += 1
            # 添加随机延迟，避免请求过于频繁
            time.sleep(random.randint(1, 3))
        
        # 打印结果摘要
        logger.info("\n=== 搜索结果 ===")
        logger.info(f"状态: 成功")
        logger.info(f"总页数: {total_pages}")
        logger.info(f"总商品数: {len(total_products)}")
        
        # 构造完整的响应数据
        complete_response = {
            'success': True,
            'code': 200,
            'msg': 'ok',
            'data': {
                'total': len(total_products),
                'items': total_products
            }
        }
        
        # 保存结果到数据库
        save_result(complete_response, logger)
        
        logger.info("=" * 60)
        logger.info(f"🎉 本次任务完成，成功获取 {len(total_products)} 个商品信息")
        logger.info("=" * 60)
        
    except Exception as e:
        error_msg = f"获取商品列表任务失败: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)

def main():
    logger.info("Starting main function")
    
    # 初始化商品服务
    product_service = ProductClient(logger=logger)
    
    # 创建任务调度器
    try:
        scheduler = TaskScheduler(
            timezone=settings.TIMEZONE,
            logger=logger
        )
        
        # 添加每分钟执行的任务
        # scheduler.add_minute_task(fetch_products_task, product_service, logger)
        scheduler.add_hourly_task(fetch_products_task, random.randint(0, 15), product_service, logger)

        
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
        logger.error(error_msg)
        sys.exit(1) 