import os
import sys
import logging

def setup_worker_logging(base_dir: str, logger_name: str = 'scheduler_worker', include_generate_articles: bool = True):
    """
    配置 worker 进程的日志系统
    
    Args:
        base_dir: 项目根目录
        logger_name: 主日志器名称
        include_generate_articles: 是否包含文章生成器的日志配置
    
    Returns:
        tuple: (主日志器, 文章生成日志器) 如果 include_generate_articles 为 False，则第二个返回值为 None
    """
    # 配置日志目录
    log_dir = os.path.join(base_dir, 'logs')
    os.makedirs(log_dir, exist_ok=True)

    # 配置日志格式
    log_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s')

    # 创建一个处理器，将 INFO 级别日志输出到 stdout
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setLevel(logging.INFO)
    stdout_handler.addFilter(lambda record: record.levelno == logging.INFO)  # 只允许 INFO 级别
    stdout_handler.setFormatter(log_format)

    # 创建一个处理器，将 WARNING 及以上级别日志输出到 stderr
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.WARNING)  # WARNING 及以上级别
    stderr_handler.setFormatter(log_format)

    # 创建文件处理器
    file_handler = logging.FileHandler(os.path.join(log_dir, 'scheduler.log'))
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(log_format)

    # 配置根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(stdout_handler)
    root_logger.addHandler(stderr_handler)
    root_logger.addHandler(file_handler)

    # 获取主日志器
    main_logger = logging.getLogger(logger_name)

    # 配置文章生成日志器（如果需要）
    articles_logger = None
    if include_generate_articles:
        articles_logger = logging.getLogger('generate_articles')
        articles_logger.setLevel(logging.INFO)
        # 清除可能存在的旧处理器
        articles_logger.handlers.clear()
        # 只添加对应级别的处理器
        articles_logger.addHandler(stdout_handler)  # INFO 级别
        articles_logger.addHandler(stderr_handler)  # WARNING 及以上级别
        articles_logger.propagate = False  # 防止日志传播到根日志器

    return main_logger, articles_logger 