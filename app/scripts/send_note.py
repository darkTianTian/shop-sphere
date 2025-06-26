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
from app.models.product import ArticleVideoMapping, Product, ProductArticle, ArticleStatus
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

# 获取环境信息
SERVER_ENV = os.environ.get('SERVER_ENVIRONMENT', 'LOCAL')

# 设置日志
try:
    logger = setup_logger(
        name='send_note',
        log_file=None,  # 不输出到文件，让supervisor处理
        level=logging.INFO
    )
except Exception as e:
    error_msg = f"设置日志失败: {str(e)}\n{traceback.format_exc()}"
    print(error_msg, file=sys.stderr)  # 直接打印到stderr
    sys.exit(1)

logger.info(f"Starting send_note in {SERVER_ENV} environment")
logger.info(f"Current PYTHONPATH: {os.environ.get('PYTHONPATH', 'Not set')}")
logger.info(f"Current working directory: {os.getcwd()}")

# 通过settings.load_settings()动态加载配置
try:
    settings = load_settings()
    logger.info("Successfully loaded settings")
except Exception as e:
    error_msg = f"加载设置失败: {str(e)}\n{traceback.format_exc()}"
    logger.error(error_msg)
    sys.exit(1)

def process_pending_articles():
    """处理待发布的文章"""
    current_time = int(time.time() * 1000)

    try:
        note_service = NoteService(logger=logger)
        
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

            logger.info(f"查询到{len(articles)}条待发布文章")
            
            for article in articles:
                try:
                    # 查询关联的商品
                    product = session.exec(select(Product).where(Product.item_id == article.item_id)).first()
                    if not product:
                        logger.error(f"文章 {article.id} 找不到关联的商品: {article.item_id}")
                        continue
                    
                    # 发送笔记
                    logger.info(f"开始发送文章 {article.id}， 商品 {product.item_id}， 标题 {article.title} 到小红书")
                    #TODO: 这里用了商品的名称，而不是sku的名称
                    response, video = note_service.send_note(article, product.first_sku_id, product.item_name)
                    
                    if response.get("success", False) and video:
                        
                        # 更新文章状态
                        article.publish_time = current_time
                        article.status = ArticleStatus.PUBLISHED
                        
                        # 更新视频发布次数
                        video.publish_cnt += 1
                        
                        # 创建文章和视频的关联记录
                        mapping = ArticleVideoMapping(
                            article_id=article.id,
                            video_id=video.id,
                            status="published",
                            publish_time=current_time
                        )
                        
                        # 保存所有更改
                        session.add(video)
                        session.add(article)
                        session.add(mapping)
                        session.commit()
                        
                        logger.info(f"文章-【{article.id}】， 商品-【{product.item_id}】， 标题-【{article.title}】 发布成功")
                    else:
                        if not video:
                            logger.info(f"文章-【{article.id}】， 商品-【{product.item_id}】， 标题-【{article.title}】 发布终止: 没有找到可用视频")
                            continue
                        error_msg = response.get("message", "未知错误")
                        logger.error(f"文章-【{article.id}】， 商品-【{product.item_id}】， 标题-【{article.title}】 发布失败: {error_msg}")
                    
                except Exception as e:
                    logger.error(f"处理文章-{article.id}， 商品-{product.item_id}， 标题-{article.title} 时出错: {str(e)}")
                    continue
            
    except Exception as e:
        logger.error(f"处理待发布文章时出错: {str(e)}")
    finally:
        note_service.close()

def main():
    """主函数"""
    logger.info("笔记发送服务启动")
    
    while True:
        try:
            process_pending_articles()
        except Exception as e:
            logger.error(f"处理文章时发生错误: {str(e)}")
        
        # 等待一段时间再次检查
        time.sleep(60)  # 每分钟检查一次

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        error_msg = f"Main function failed: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        sys.exit(1)