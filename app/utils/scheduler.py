import time
import logging
from datetime import datetime
from typing import Callable, Optional
import pytz
from schedule import Scheduler


class TaskScheduler:
    """任务调度器"""
    
    def __init__(self, timezone: str = 'Asia/Shanghai', logger: Optional[logging.Logger] = None):
        self.timezone = pytz.timezone(timezone)
        self.logger = logger or logging.getLogger(__name__)
        self.scheduler = Scheduler()
        self._running = False
        
    def add_minute_task(self, task_func: Callable, *args, **kwargs):
        """添加每分钟执行的任务"""
        def wrapped_task():
            try:
                current_time = datetime.now(self.timezone).strftime("%Y-%m-%d %H:%M:%S")
                self.logger.info(f"执行定时任务 at {current_time}")
                task_func(*args, **kwargs)
            except Exception as e:
                self.logger.error(f"任务执行失败: {str(e)}")
                
        self.scheduler.every().minute.at(":00").do(wrapped_task)
        
    def add_hourly_task(self, task_func: Callable, minute: int = 0, *args, **kwargs):
        """添加每小时执行的任务"""
        def wrapped_task():
            try:
                current_time = datetime.now(self.timezone).strftime("%Y-%m-%d %H:%M:%S")
                self.logger.info(f"执行小时任务 at {current_time}")
                task_func(*args, **kwargs)
            except Exception as e:
                self.logger.error(f"任务执行失败: {str(e)}")
                
        self.scheduler.every().hour.at(f":{minute:02d}").do(wrapped_task)
        
    def add_daily_task(self, task_func: Callable, time_str: str = "00:00", *args, **kwargs):
        """添加每日执行的任务"""
        def wrapped_task():
            try:
                current_time = datetime.now(self.timezone).strftime("%Y-%m-%d %H:%M:%S")
                self.logger.info(f"执行日常任务 at {current_time}")
                task_func(*args, **kwargs)
            except Exception as e:
                self.logger.error(f"任务执行失败: {str(e)}")
                
        self.scheduler.every().day.at(time_str).do(wrapped_task)
        
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
        
        # 等待到下一分钟的整点再开始
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