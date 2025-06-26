#!/usr/bin/env python3
import os
import sys
import logging
from datetime import datetime, time as datetime_time
import time
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlmodel import Session, select

from app.internal.db import engine
from app.models.publish_config import PublishConfig
from app.scripts.generate_product_articles import ProductArticleGenerator
from app.settings.logging_config import setup_worker_logging

# 获取项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 设置日志
logger, generate_articles_logger = setup_worker_logging(BASE_DIR)

class SchedulerWorker:
    def __init__(self, timezone: str = 'Asia/Shanghai'):
        self.timezone = pytz.timezone(timezone)
        # 配置 APScheduler 以支持 Docker 环境
        self.scheduler = BackgroundScheduler(
            timezone=timezone,
            job_defaults={
                'coalesce': True,  # 合并延迟的任务
                'max_instances': 1,  # 最大实例数
                'misfire_grace_time': 60  # 任务错过执行时间的容错范围（秒）
            }
        )
        self.article_job_id = 'generate_articles'
        self.config_check_job_id = 'check_config'
        self._last_generate_time = None
        
    def check_config_updates(self):
        """检查配置是否有更新"""
        try:
            with Session(engine) as session:
                config = session.exec(select(PublishConfig)).first()
                if not config:
                    return
                
                # 如果生成时间有变化，重新加载任务
                if self._last_generate_time != config.generate_time:
                    logger.info(f"检测到生成时间更新: {config.generate_time.strftime('%H:%M')}")
                    self._last_generate_time = config.generate_time
                    self.update_article_generation_job()
        except Exception as e:
            logger.error(f"检查配置更新失败: {str(e)}")
        
    def update_article_generation_job(self):
        """更新文章生成任务的执行时间"""
        with Session(engine) as session:
            config = session.exec(select(PublishConfig)).first()
            if not config:
                return
            
            # 获取生成时间
            generate_time = config.generate_time
            self._last_generate_time = generate_time
            
            # 如果任务已存在，先移除
            if self.scheduler.get_job(self.article_job_id):
                self.scheduler.remove_job(self.article_job_id)
            
            # 创建新任务
            if config.is_enabled:
                trigger = CronTrigger(
                    hour=generate_time.hour,
                    minute=generate_time.minute,
                    timezone=self.timezone
                )
                
                def run_task():
                    generator = ProductArticleGenerator(logger=generate_articles_logger)
                    generator.run_generation_task()
                
                self.scheduler.add_job(
                    run_task,
                    trigger=trigger,
                    id=self.article_job_id,
                    name='Generate Product Articles',
                    max_instances=1,
                    coalesce=True
                )
                
                logger.info(f"已更新文章生成任务，执行时间: {generate_time.strftime('%H:%M')}")
            else:
                logger.info("文章生成任务已禁用")
    
    def start(self):
        """启动调度器"""
        try:
            if not self.scheduler.running:
                # 初始化任务
                self.update_article_generation_job()
                
                # 添加配置检查任务（每分钟检查一次）
                self.scheduler.add_job(
                    self.check_config_updates,
                    'interval',
                    minutes=1,
                    id=self.config_check_job_id,
                    name='Check Configuration Updates'
                )
                
                # 启动调度器
                self.scheduler.start()
                logger.info("调度器已启动")
                
                # 保持进程运行
                try:
                    while True:
                        self.scheduler.print_jobs()
                        time.sleep(60)  # 每分钟打印一次任务状态
                except KeyboardInterrupt:
                    logger.info("收到中断信号")
                    self.stop()
        except Exception as e:
            logger.error(f"调度器运行异常: {str(e)}")
            self.stop()
            sys.exit(1)
    
    def stop(self):
        """停止调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("调度器已停止")

def main():
    # 创建并启动调度器
    worker = SchedulerWorker()
    worker.start()

if __name__ == '__main__':
    main() 