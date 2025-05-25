#!/usr/bin/env python3
import sys
import os
from datetime import datetime
import pytz

# 获取环境信息
SERVER_ENV = os.environ.get('SERVER_ENVIRONMENT', 'LOCAL')

# 引入封装的logger
try:
    from app.utils.logger import setup_logger
    from app.utils.scheduler import TaskScheduler
    from app.services.product_service import ProductService
    from app.config.product_auth_config import ProductAuthConfig
except ImportError as e:
    print(f"导入模块失败: {e}")
    sys.exit(1)

# 通过settings.load_settings()动态加载配置
try:
    from app.settings import load_settings
    settings = load_settings()
except Exception as e:
    print(f"加载设置失败: {e}")
    sys.exit(1)


def fetch_products_task(product_service: ProductService, logger):
    """获取商品列表任务"""
    try:
        current_time = datetime.now(pytz.timezone(settings.TIMEZONE)).strftime("%Y-%m-%d %H:%M:%S")
        message = f"[{SERVER_ENV}] 开始获取商品列表任务 at {current_time}"
        logger.info(message)
        
        # 搜索商品列表
        response = product_service.search_products()
        
        # 打印搜索结果摘要
        product_service.print_search_summary(response)
        
        # 如果成功，额外打印一些统计信息
        if response.success and response.products:
            logger.info("=" * 60)
            logger.info(f"🎉 本次任务完成，成功获取 {len(response.products)} 个商品信息")
            
            # 统计不同状态的商品数量
            status_count = {}
            for product in response.products:
                status = product.status or 'unknown'
                status_count[status] = status_count.get(status, 0) + 1
            
            if status_count:
                logger.info("📊 商品状态统计:")
                for status, count in status_count.items():
                    logger.info(f"  {status}: {count} 个")
        
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"获取商品列表任务失败: {str(e)}")


def main():
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
    except Exception as e:
        print(f"设置日志失败: {e}")
        sys.exit(1)
        
    logger.info(f"Product fetch service started in {SERVER_ENV} environment")
    
    # 初始化商品服务
    product_service = ProductService(logger=logger)
    
    # 设置认证信息
    try:
        # 优先从环境变量加载认证配置
        auth_config = ProductAuthConfig.from_env()
        if auth_config is None:
            # 如果环境变量没有配置，使用默认配置
            logger.warning("未找到环境变量中的商品API认证配置，使用默认配置")
            auth_config = ProductAuthConfig.get_default()
            
        product_service.setup_auth(
            authorization=auth_config.authorization,
            x_s=auth_config.x_s,
            x_t=auth_config.x_t,
            cookie=auth_config.cookie
        )
        logger.info("商品API认证配置设置完成")
        
    except Exception as e:
        logger.error(f"设置商品API认证配置失败: {str(e)}")
        sys.exit(1)
    
    # 创建任务调度器
    try:
        scheduler = TaskScheduler(
            timezone=settings.TIMEZONE,
            logger=logger
        )
        
        # 添加每分钟执行的任务
        scheduler.add_minute_task(fetch_products_task, product_service, logger)
        
        logger.info("已添加每分钟获取商品列表的定时任务")
        
        # 启动调度器
        scheduler.start()
        
    except KeyboardInterrupt:
        logger.info("Product fetch service stopped by user")
        product_service.close()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        product_service.close()
        sys.exit(1)


if __name__ == "__main__":
    main() 