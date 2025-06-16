#!/usr/bin/env python3
import logging
import sys
import os
from datetime import datetime
import pytz
import traceback

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 设置基本的错误日志
base_logger = logging.getLogger('send_note')
base_logger.setLevel(logging.INFO)
base_logger.propagate = False  # 防止日志传播到父logger

# 获取环境信息
SERVER_ENV = os.environ.get('SERVER_ENVIRONMENT', 'LOCAL')
base_logger.info(f"Starting send_note in {SERVER_ENV} environment")
base_logger.info(f"Current PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
base_logger.info(f"Current working directory: {os.getcwd()}")

# 引入封装的logger
try:
    from app.utils.logger import setup_logger
    from app.utils.scheduler import TaskScheduler
    from app.services.xiaohongshu.note_service import NoteService
    from app.config.auth_config import AuthConfig
except ImportError as e:
    error_msg = f"导入模块失败: {str(e)}\n{traceback.format_exc()}"
    base_logger.error(error_msg)
    sys.exit(1)

# 通过settings.load_settings()动态加载配置
try:
    from app.settings import load_settings
    settings = load_settings()
    base_logger.info("Successfully loaded settings")
except Exception as e:
    error_msg = f"加载设置失败: {str(e)}\n{traceback.format_exc()}"
    base_logger.error(error_msg)
    sys.exit(1)

def send_note_task(note_service: NoteService, logger):
    """发送笔记任务"""
    try:
        current_time = datetime.now(pytz.timezone(settings.TIMEZONE)).strftime("%Y-%m-%d %H:%M:%S")
        message = f"[{SERVER_ENV}] 开始发送笔记任务 at {current_time}"
        logger.info(message)
        
        # 获取商品ID
        goods_id = "6751b6543940240001f77911"
        # 发送笔记
        response = note_service.send_note(goods_id)
        
        # 打印结果摘要
        logger.info("\n=== 发送结果 ===")
        logger.info(f"状态: {'成功' if response.get('success') else '失败'}")
        logger.info(f"代码: {response.get('code')}")
        logger.info(f"消息: {response.get('msg')}")
        
        logger.info("=" * 60)
        
    except Exception as e:
        error_msg = f"发送笔记任务失败: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)

def main():
    base_logger.info("Starting main function")
    
    # 使用supervisor配置的日志路径
    log_file = '/var/log/supervisor/send_note_out.log'
    
    # 使用封装的logger
    try:
        logger = setup_logger(
            name=f'send_note_{SERVER_ENV.lower()}',
            log_file=log_file,
            level=20,  # logging.INFO
            log_to_stderr=False  # 修改这里，因为supervisor已经处理了日志重定向
        )
        logger.propagate = False  # 防止日志传播到父logger
        logger.info("Logger setup completed")
    except Exception as e:
        error_msg = f"设置日志失败: {str(e)}\n{traceback.format_exc()}"
        base_logger.error(error_msg)
        sys.exit(1)
        
    logger.info(f"Note send service started in {SERVER_ENV} environment")
    
    # 初始化笔记服务
    note_service = NoteService(logger=logger)
    
    
    # 创建任务调度器
    try:
        scheduler = TaskScheduler(
            timezone=settings.TIMEZONE,
            logger=logger
        )
        
        # 添加定时任务
        # # 每天上午10点和下午3点发送笔记
        # scheduler.add_daily_task(send_note_task, hour=10, minute=0, args=(note_service, logger))
        # scheduler.add_daily_task(send_note_task, hour=15, minute=0, args=(note_service, logger))
        scheduler.add_minute_task(send_note_task, note_service, logger)
        
        logger.info("已添加定时发送笔记任务")
        
        # 启动调度器
        scheduler.start()
        
    except KeyboardInterrupt:
        logger.info("Note send service stopped by user")
        sys.exit(0)
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        error_msg = f"Main function failed: {str(e)}\n{traceback.format_exc()}"
        base_logger.error(error_msg)
        sys.exit(1)