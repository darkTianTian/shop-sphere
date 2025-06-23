#!/usr/bin/env python3
import logging
import sys
import os
from datetime import datetime
import pytz
import traceback
import time
from sqlmodel import Session, select
from app.internal.db import engine
from app.models.product import Product, ProductArticle, ArticleStatus
from app.services.xiaohongshu.note_service import NoteService
from app.settings import load_settings

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 引入封装的logger
try:
    from app.utils.logger import setup_logger
    from app.utils.scheduler import TaskScheduler
    from app.config.auth_config import AuthConfig
except ImportError as e:
    error_msg = f"导入模块失败: {str(e)}\n{traceback.format_exc()}"
    sys.exit(1)

# 设置日志
base_logger = setup_logger(
    name='send_note',
    log_file=None,  # 不输出到文件，只输出到控制台，由supervisor管理
    level=20  # INFO
)

# 获取环境信息
SERVER_ENV = os.environ.get('SERVER_ENVIRONMENT', 'LOCAL')
base_logger.info(f"Starting send_note in {SERVER_ENV} environment")
base_logger.info(f"Current PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
base_logger.info(f"Current working directory: {os.getcwd()}")

# 通过settings.load_settings()动态加载配置
try:
    settings = load_settings()
    base_logger.info("Successfully loaded settings")
except Exception as e:
    error_msg = f"加载设置失败: {str(e)}\n{traceback.format_exc()}"
    base_logger.error(error_msg)
    sys.exit(1)

def process_pending_articles():
    """处理待发布的文章"""
    note_service = NoteService(logger=base_logger)
    current_time = int(time.time() * 1000)  # 当前时间戳（毫秒）
    
    try:
        with Session(engine) as session:
            # 查询预发布时间小于当前时间的文章，按预发布时间递增排序
            query = select(ProductArticle).where(
                ProductArticle.status == ArticleStatus.PENDING_PUBLISH,
                ProductArticle.pre_publish_time > 0,  # 确保设置了预发布时间
                ProductArticle.pre_publish_time <= current_time,  # 预发布时间已到
                ProductArticle.publish_time == 0  # 尚未发布
            ).order_by(ProductArticle.pre_publish_time).limit(5)
            
            # 查询5条数据
            articles = session.exec(query).all()
            
            for article in articles:
                try:
                    # 查询关联的商品
                    product = session.exec(select(Product).where(Product.item_id == article.item_id)).first()
                    if not product:
                        base_logger.error(f"文章 {article.id} 找不到关联的商品: {article.item_id}")
                        continue
                    
                    # 发送笔记
                    base_logger.info(f"开始发送文章 {article.id}， 商品 {product.item_id}， 标题 {article.title} 到小红书")
                    #TODO: 这里用了商品的名称，而不是sku的名称
                    success = note_service.send_note(article, product.first_sku_id, product.item_name)
                    
                    if success:
                        # 更新文章状态
                        article.publish_time = int(time.time() * 1000)
                        article.status = ArticleStatus.PUBLISHED
                        # TODO：更新视频发布次数
                        session.add(article)
                        session.commit()
                        base_logger.info(f"文章-【{article.id}】， 商品-【{product.item_id}】， 标题-【{article.title}】 发布成功")
                    else:
                        base_logger.error(f"文章-{article.id}， 商品-{product.item_id}， 标题-{article.title} 发布失败")
                        
                except Exception as e:
                    base_logger.error(f"处理文章-{article.id}， 商品-{product.item_id}， 标题-{article.title} 时出错: {str(e)}")
                    continue
                    
    except Exception as e:
        base_logger.error(f"查询待发布文章时出错: {str(e)}")

def main():
    """主函数"""
    base_logger.info("笔记发送服务启动")
    
    while True:
        try:
            process_pending_articles()
        except Exception as e:
            base_logger.error(f"处理文章时发生错误: {str(e)}")
        
        # 等待一段时间再次检查
        time.sleep(60)  # 每分钟检查一次

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        error_msg = f"Main function failed: {str(e)}\n{traceback.format_exc()}"
        base_logger.error(error_msg)
        sys.exit(1)