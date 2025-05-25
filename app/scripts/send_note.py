#!/usr/bin/env python3
import time
import sys
import os
import schedule
from datetime import datetime

# 引入封装的logger
from app.utils.logger import setup_logger

def job(logger):
    """每分钟执行的任务"""
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    message = f"hello world at {current_time}"
    logger.info(message)

def main():
    # 使用封装的logger
    logger = setup_logger(
        name='send_note',
        log_file='/var/log/supervisor/send_note_out.log',
        level=20,  # logging.INFO
        log_to_stderr=True
    )
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