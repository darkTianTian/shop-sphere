#!/usr/bin/env python3
import time
import sys
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

# 配置日志
def setup_logger():
    logger = logging.getLogger('send_note')
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
    
    # 添加控制台输出
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

def main():
    logger = setup_logger()
    logger.info("Service started")
    
    try:
        while True:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message = f"hello world at {current_time}"
            print(message)  # 直接打印到控制台
            logger.info(message)  # 同时记录到日志
            time.sleep(60)  # 每分钟执行一次
            
    except KeyboardInterrupt:
        logger.info("Service stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()