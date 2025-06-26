import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional

class MaxLevelFilter(logging.Filter):
    """日志过滤器，允许不高于指定级别的日志通过"""
    def __init__(self, level: int):
        super().__init__()
        self.level = level

    def filter(self, record: logging.LogRecord) -> bool:  # noqa: D401
        return record.levelno <= self.level

def setup_logger(name: str, log_file: Optional[str] = None, level: int = logging.INFO) -> logging.Logger:
    """
    设置日志记录器
    
    Args:
        name: 日志记录器名称
        log_file: 日志文件路径，如果为None则只输出到控制台
        level: 日志级别
        
    Returns:
        配置好的日志记录器
    """
    # 创建logger
    logger = logging.getLogger(name)
    
    # 清除所有现有的处理器
    if logger.hasHandlers():
        logger.handlers.clear()
    
    # 设置基本配置
    logger.setLevel(level)
    logger.propagate = False
    
    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
    
    if log_file:
        # 文件处理器
        try:
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            print(f"无法创建日志文件处理器: {str(e)}", file=sys.stderr)
    else:
        # INFO及以下级别的日志输出到stdout
        stdout_handler = logging.StreamHandler(sys.stdout)
        stdout_handler.setFormatter(formatter)
        stdout_handler.setLevel(logging.DEBUG)
        stdout_handler.addFilter(MaxLevelFilter(logging.INFO))
        logger.addHandler(stdout_handler)
        
        # WARNING及以上级别的日志输出到stderr
        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setFormatter(formatter)
        stderr_handler.setLevel(logging.WARNING)
        logger.addHandler(stderr_handler)
    
    return logger 