#!/usr/bin/env python3
import sys
import os
from datetime import datetime
import pytz

# 获取环境信息
SERVER_ENV = os.environ.get('SERVER_ENVIRONMENT', 'LOCAL')

# 引入封装的logger
try:
    from app.utils.logger import setup_logger
    from app.utils.scheduler import TaskScheduler
    from app.services.note_service import NoteService
    from app.config.auth_config import AuthConfig
except ImportError as e:
    print(f"导入模块失败: {e}")
    sys.exit(1)

# 通过settings.load_settings()动态加载配置
try:
    from app.settings import load_settings
    settings = load_settings()
except Exception as e:
    print(f"加载设置失败: {e}")
    sys.exit(1)


def send_note_task(note_service: NoteService, logger):
    """发送笔记任务"""
    try:
        current_time = datetime.now(pytz.timezone(settings.TIMEZONE)).strftime("%Y-%m-%d %H:%M:%S")
        message = f"[{SERVER_ENV}] 开始发送笔记任务 at {current_time}"
        logger.info(message)
        
        # 发送笔记
        response = note_service.send_note()
        logger.info(f"笔记发送响应: {response}")
        
    except Exception as e:
        logger.error(f"发送笔记任务失败: {str(e)}")


def main():
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
    except Exception as e:
        print(f"设置日志失败: {e}")
        sys.exit(1)
        
    logger.info(f"Service started in {SERVER_ENV} environment")
    
    # 初始化笔记服务
    note_service = NoteService(logger=logger)
    
    # 设置认证信息
    try:
        # 优先从环境变量加载认证配置
        auth_config = AuthConfig.from_env()
        if auth_config is None:
            # 如果环境变量没有配置，使用默认配置
            logger.warning("未找到环境变量中的认证配置，使用默认配置")
            auth_config = AuthConfig.get_default()
            
        note_service.setup_auth(
            cookie=auth_config.cookie,
            x_s=auth_config.x_s,
            x_t=auth_config.x_t
        )
        logger.info("认证配置设置完成")
        
    except Exception as e:
        logger.error(f"设置认证配置失败: {str(e)}")
        sys.exit(1)
    
    # 创建任务调度器
    try:
        scheduler = TaskScheduler(
            timezone=settings.TIMEZONE,
            logger=logger
        )
        
        # 添加每分钟执行的任务
        scheduler.add_minute_task(send_note_task, note_service, logger)
        
        # 启动调度器
        scheduler.start()
        
    except KeyboardInterrupt:
        logger.info("Service stopped by user")
        note_service.close()
        sys.exit(0)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        note_service.close()
        sys.exit(1)


if __name__ == "__main__":
    main()