#!/usr/bin/env python3
"""
自动生成商品文章的定时脚本
每分钟执行一次，为符合条件的商品生成文章草稿
"""

import os
import sys
import time
import traceback
from datetime import datetime, timedelta
import asyncio
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlmodel import select
import logging

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.internal.db import get_async_session
from app.models.publish_config import PublishConfig
from app.scripts.generate_product_articles import ProductArticleGenerator
from app.utils.logger import setup_logger

# 设置日志
logger = setup_logger(
    name='scheduler_worker',
    log_file=None,  # 不输出到文件，只输出到控制台
    level=logging.INFO  # INFO级别
)

class SchedulerWorker:
    def __init__(self, timezone: str = 'Asia/Shanghai'):
        self.timezone = timezone
        self.scheduler = AsyncIOScheduler(timezone=timezone)
        self.generator = ProductArticleGenerator(logger=logger, max_concurrent=5)
        
    async def check_and_run_task(self):
        """检查配置并执行任务"""
        try:
            async with get_async_session() as session:
                # 获取发布配置
                config = (await session.execute(select(PublishConfig))).scalars().first()
                if not config or not config.is_enabled:
                    logger.info("发布配置未启用，跳过文章生成")
                    return
                
                # 检查是否在生成时间
                now = datetime.now(pytz.timezone(self.timezone))
                generate_time = config.generate_time
                current_time = now.time()
                
                # 如果当前时间在生成时间的前后5分钟内，执行生成任务
                time_diff = abs((current_time.hour * 60 + current_time.minute) - 
                              (generate_time.hour * 60 + generate_time.minute))
                
                if time_diff <= 5:  # 5分钟内
                    logger.info(f"当前时间 {current_time} 接近生成时间 {generate_time}，开始执行生成任务")
                    await self.generator.run_generation_task()
                else:
                    logger.info(f"当前时间 {current_time} 不在生成时间 {generate_time} 附近，跳过执行")
                    
        except Exception as e:
            error_msg = f"执行定时任务失败: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
    
    async def start(self):
        """启动调度器"""
        try:
            # 添加每分钟执行的任务
            self.scheduler.add_job(
                self.check_and_run_task,
                CronTrigger(minute='*/3'),  # 每分钟执行一次
                id='generate_articles',
                replace_existing=True,
                max_instances=1,  # 最多允许1个实例运行
                coalesce=True     # 如果错过执行时间，合并执行
            )
            
            # 启动调度器
            self.scheduler.start()
            logger.info("调度器已启动，每分钟检查一次是否需要生成文章")
            
            # 保持运行直到收到停止信号
            while True:
                await asyncio.sleep(60)
                
        except Exception as e:
            error_msg = f"启动调度器失败: {str(e)}\n{traceback.format_exc()}"
            logger.error(error_msg)
            raise
        
    def stop(self):
        """停止调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("调度器已停止")

async def main_async():
    """异步主函数"""
    try:
        logger.info("启动商品文章生成定时任务")
        worker = SchedulerWorker()
        await worker.check_and_run_task()
    except Exception as e:
        error_msg = f"任务执行失败: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        sys.exit(1)

def main():
    """主函数"""
    try:
        logger.info("启动商品文章生成定时任务")
        # 创建新的事件循环并设为当前
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # 在事件循环就绪后再创建 worker（内部对象会绑定到正确的 loop）
        worker = SchedulerWorker()
        
        try:
            # 运行调度器
            loop.run_until_complete(worker.start())
        except KeyboardInterrupt:
            logger.info("收到中断信号，正在停止定时任务...")
            worker.stop()
        finally:
            loop.close()
            
    except Exception as e:
        error_msg = f"定时任务启动失败: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        sys.exit(1)

if __name__ == "__main__":
    main() 