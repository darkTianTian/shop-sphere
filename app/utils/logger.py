import logging
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional

def setup_logger(
    name: str = 'app',
    log_file: Optional[str] = None,
    level: int = logging.INFO,
    log_to_stderr: bool = True,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5
) -> logging.Logger:
    """
    封装的日志初始化方法。
    :param name: logger名称
    :param log_file: 日志文件路径（可选）
    :param level: 日志级别
    :param log_to_stderr: 是否输出到标准错误
    :param max_bytes: 单个日志文件最大字节数
    :param backup_count: 日志文件保留个数
    :return: logger实例
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 清理已存在的日志处理器
    if logger.hasHandlers():
        logger.handlers.clear()

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )

    if log_file:
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    if log_to_stderr:
        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setFormatter(formatter)
        logger.addHandler(stderr_handler)

    return logger 