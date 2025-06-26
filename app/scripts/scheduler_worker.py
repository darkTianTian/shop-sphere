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

# 获取项目根目录
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置日志目录
LOG_DIR = os.path.join(BASE_DIR, 'logs')
os.makedirs(LOG_DIR, exist_ok=True)

# 配置日志格式
log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')

# 创建一个处理器，将 INFO 级别日志输出到 stdout
stdout_handler = logging.StreamHandler(sys.stdout)
stdout_handler.setLevel(logging.INFO)
stdout_handler.addFilter(lambda record: record.levelno == logging.INFO)  # 只允许 INFO 级别
stdout_handler.setFormatter(log_format)

# 创建一个处理器，将 WARNING 及以上级别日志输出到 stderr
stderr_handler = logging.StreamHandler(sys.stderr)
stderr_handler.setLevel(logging.WARNING)  # WARNING 及以上级别
stderr_handler.setFormatter(log_format)

# 创建文件处理器
file_handler = logging.FileHandler(os.path.join(LOG_DIR, 'scheduler.log'))
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(log_format)

# 配置根日志器
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(stdout_handler)
root_logger.addHandler(stderr_handler)
root_logger.addHandler(file_handler)

# 获取调度器专用的日志器
logger = logging.getLogger('scheduler_worker')

# 配置 generate_articles 日志器
generate_articles_logger = logging.getLogger('generate_articles')
generate_articles_logger.setLevel(logging.INFO)
# 清除可能存在的旧处理器
generate_articles_logger.handlers.clear()
# 只添加对应级别的处理器
generate_articles_logger.addHandler(stdout_handler)  # INFO 级别
generate_articles_logger.addHandler(stderr_handler)  # WARNING 及以上级别
generate_articles_logger.propagate = False  # 防止日志传播到根日志器

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
    # 确保日志目录存在
    os.makedirs(LOG_DIR, exist_ok=True)
    
    # 创建并启动调度器
    worker = SchedulerWorker()
    worker.start()

if __name__ == '__main__':
    main() 