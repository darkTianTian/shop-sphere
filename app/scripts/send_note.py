#!/usr/bin/env python3
import time
import sys
import os
import logging
import schedule
from logging.handlers import RotatingFileHandler
from datetime import datetime

def setup_logger():
    # 清理已存在的日志处理器
    logger = logging.getLogger('send_note')
    if logger.handlers:
        for handler in logger.handlers:
            logger.removeHandler(handler)
    
    logger.setLevel(logging.INFO)
    
    # 确保日志目录存在
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # 创建一个rotating文件处理器
    log_file = os.path.join(log_dir, 'send_note.log')
    handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger

def job(logger):
    """每分钟执行的任务"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"hello world at {current_time}"
    logger.info(message)

def main():
    logger = setup_logger()
    logger.info("Service started")
    
    try:
        # 设置定时任务，每分钟整点执行
        schedule.every().minute.at(":00").do(job, logger)
        
        # 等待到下一分钟的整点再开始
        current_time = datetime.now()
        seconds_to_wait = 60 - current_time.second
        time.sleep(seconds_to_wait)
        
        while True:
            schedule.run_pending()
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Service stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()