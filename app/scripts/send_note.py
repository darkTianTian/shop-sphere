#!/usr/bin/env python3
import time
import sys
import os
from datetime import datetime
import pytz
from schedule import Scheduler

# 获取环境信息
SERVER_ENV = os.environ.get('SERVER_ENVIRONMENT', 'LOCAL')

# 引入封装的logger
try:
    from app.utils.logger import setup_logger
except ImportError as e:
    sys.exit(1)

# 通过settings.load_settings()动态加载配置
try:
    from app.settings import load_settings
    settings = load_settings()
except Exception as e:
    sys.exit(1)

# 设置统一时区
TZ = pytz.timezone(settings.TIMEZONE)

def job(logger):
    """每分钟执行的任务"""
    try:
        current_time = datetime.now(TZ).strftime("%Y-%m-%d %H:%M:%S")
        message = f"[{SERVER_ENV}] hello world at {current_time}"
        logger.info(message)
    except Exception as e:
        logger.error(f"Error in job: {str(e)}")

def main():
    # 使用supervisor配置的日志路径
    log_file = '/var/log/supervisor/send_note_out.log'
    
    # 使用封装的logger，在Docker环境中不输出到stderr（避免重复日志）
    try:
        logger = setup_logger(
            name=f'send_note_{SERVER_ENV.lower()}',
            log_file=log_file,
            level=20,  # logging.INFO
            log_to_stderr=False  # 修改这里，因为supervisor已经处理了日志重定向
        )
    except Exception as e:
        sys.exit(1)
        
    logger.info(f"Service started in {SERVER_ENV} environment")
    
    try:
        # 创建独立的scheduler实例
        scheduler = Scheduler()
        
        # 设置定时任务，每分钟整点执行
        scheduler.every().minute.at(":00").do(job, logger)
        
        # 等待到下一分钟的整点再开始
        current_time = datetime.now(TZ)
        seconds_to_wait = 60 - current_time.second
        time.sleep(seconds_to_wait)
        
        while True:
            scheduler.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Service stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()