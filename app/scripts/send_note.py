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
    
    # 使用supervisor配置的日志路径
    log_file = '/var/log/supervisor/send_note_out.log'
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
    
    # 添加标准错误输出处理器
    error_handler = logging.StreamHandler(sys.stderr)
    error_handler.setFormatter(formatter)
    logger.addHandler(error_handler)
    
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