import time
import logging
from datetime import datetime, timedelta
from typing import Callable, Optional
import pytz
from schedule import Scheduler
import requests
import os

class TaskScheduler:
    """任务调度器 - 用于固定间隔任务，动态任务由独立的调度器进程处理"""
    
    def __init__(self, timezone: str = 'Asia/Shanghai', logger: Optional[logging.Logger] = None):
        self.timezone = pytz.timezone(timezone)
        self.logger = logger or logging.getLogger(__name__)
        self.scheduler = Scheduler()
        self._running = False
        
    def _log_next_execution(self, job):
        """记录下次执行时间"""
        if job.next_run:
            current_time = datetime.now(self.timezone)
            
            # 根据任务间隔计算下次执行时间
            if job.unit == 'minutes':
                next_run = current_time.replace(second=0, microsecond=0) + timedelta(minutes=job.interval)
            elif job.unit == 'hours':
                next_run = current_time.replace(minute=0, second=0, microsecond=0) + timedelta(hours=job.interval)
            elif job.unit == 'days':
                next_run = current_time.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=job.interval)
            else:
                return
                
            self.logger.info(f"⏰ 下次执行时间: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")

    def update_article_generation_job(self):
        """更新文章生成任务的执行时间 - 通过独立调度器处理"""
        # 这里我们不再直接管理文章生成任务
        # 它会由独立的调度器进程处理
        pass
        
    def add_minute_task(self, task_func: Callable, *args, **kwargs):
        """添加每分钟执行的任务"""
        def wrapped_task():
            try:
                current_time = datetime.now(self.timezone)
                self.logger.info(f"执行定时任务 at {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
                task_func(*args, **kwargs)
                # 记录下次执行时间
                self._log_next_execution(job)
            except Exception as e:
                self.logger.error(f"任务执行失败: {str(e)}")
                
        job = self.scheduler.every().minute.at(":00").do(wrapped_task)
        
    def add_hourly_task(self, task_func: Callable, minute: int = 0, *args, **kwargs):
        """添加每小时执行的任务"""
        def wrapped_task():
            try:
                current_time = datetime.now(self.timezone)
                self.logger.info(f"执行小时任务 at {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
                task_func(*args, **kwargs)
                # 记录下次执行时间
                self._log_next_execution(job)
            except Exception as e:
                self.logger.error(f"任务执行失败: {str(e)}")
                
        job = self.scheduler.every().hour.at(f":{minute:02d}").do(wrapped_task)
        
    def add_daily_task(self, task_func: Callable, time_str: str = "00:00", *args, **kwargs):
        """添加每日执行的任务"""
        def wrapped_task():
            try:
                current_time = datetime.now(self.timezone)
                self.logger.info(f"执行日常任务 at {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
                task_func(*args, **kwargs)
                # 记录下次执行时间
                self._log_next_execution(job)
            except Exception as e:
                self.logger.error(f"任务执行失败: {str(e)}")
                
        job = self.scheduler.every().day.at(time_str).do(wrapped_task)
        
    def wait_for_next_minute(self):
        """等待到下一分钟的整点"""
        current_time = datetime.now(self.timezone)
        seconds_to_wait = 60 - current_time.second
        self.logger.info(f"等待 {seconds_to_wait} 秒到下一分钟整点")
        time.sleep(seconds_to_wait)
        
    def start(self):
        """启动调度器"""
        self._running = True
        self.logger.info("任务调度器启动")
        
        # 等待到下一分钟的整点再开始schedule任务
        self.wait_for_next_minute()
        
        try:
            while self._running:
                self.scheduler.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("收到中断信号，停止调度器")
            self.stop()
        except Exception as e:
            self.logger.error(f"调度器运行异常: {str(e)}")
            raise
            
    def stop(self):
        """停止调度器"""
        self._running = False
        self.logger.info("任务调度器已停止")
        
    def clear_jobs(self):
        """清除所有任务"""
        self.scheduler.clear()
        self.logger.info("已清除所有任务") 

# 创建全局调度器实例
task_scheduler = TaskScheduler() 
