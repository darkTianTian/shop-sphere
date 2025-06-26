#!/usr/bin/env python3
"""
自动生成商品文章的定时脚本
每分钟执行一次，为符合条件的商品生成文章草稿
"""

import os
import sys
import time
import traceback
from datetime import datetime
from typing import List, Optional

from app.models.video import Video, VideoStatus

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select
from app.internal.db import engine
from app.models.product import Product, ProductArticle, ArticleStatus, ProductStatus
from app.services.ai_service import DeepSeekAIService
from app.utils.logger import setup_logger
from app.utils.scheduler import TaskScheduler
from app.models.publish_config import PublishConfig

# 设置日志
base_logger = setup_logger(
    name='generate_articles',
    log_file=None,  # 不输出到文件，只输出到控制台，由supervisor管理
    level=20  # INFO
)


class ProductArticleGenerator:
    """商品文章生成器"""
    
    def __init__(self, logger=None):
        self.logger = logger or base_logger
        self.ai_service = DeepSeekAIService(logger=self.logger)
        self.processed_count = 0
        self.generated_count = 0
        self.error_count = 0
    
    def get_products_needing_articles(self) -> List[Product]:
        """
        获取需要生成文章的商品列表
        且没有 DRAFT/PENDING_REVIEW/PENDING_PUBLISH 状态的文章
        """
        try:
            with Session(engine) as session:
                
                # 查询符合条件的商品
                products_query = select(Product).where(
                    Product.status == ProductStatus.MANAGED,
                ).limit(50).order_by(Product.item_create_time.desc())
                products = session.exec(products_query).all()
                
                # 过滤出需要生成文章的商品
                products_needing_articles = []
                
                for product in products:
                    # 检查是否已有指定状态的文章
                    existing_articles_query = select(ProductArticle).where(
                        ProductArticle.item_id == product.item_id,
                        ProductArticle.status.in_([
                            ArticleStatus.DRAFT,
                            ArticleStatus.PENDING_REVIEW,
                            ArticleStatus.PENDING_PUBLISH
                        ])
                    )
                    existing_articles = session.exec(existing_articles_query).all()
                    
                    # 查询商品是否存在待发布视频
                    pending_videos_query = select(Video).where(
                        Video.item_id == product.item_id,
                        Video.is_enabled == True
                    )
                    has_video = session.exec(pending_videos_query).first() is not None

                    # 如果没有这些状态的文章，则需要生成
                    if not existing_articles and has_video:
                        products_needing_articles.append(product)
                    elif not has_video:
                        self.logger.info(f"商品 {product.item_id} 没有待发布视频，跳过文章生成")
                
                self.logger.info(f"找到 {len(products)} 个符合条件的商品，其中 {len(products_needing_articles)} 个需要生成文章")
                self.logger.error(f"test error")
                self.logger.warning(f"test warning")
                return products_needing_articles
                
        except Exception as e:
            self.logger.error(f"查询需要生成文章的商品失败: {str(e)}")
            return []
    
    def generate_article_with_ai(self, product: Product) -> Optional[dict]:
        """
        使用 AI 服务生成文章内容
        
        Args:
            product: 商品对象
            
        Returns:
            包含文章内容的字典，如果生成失败则返回 None
        """
        try:
            self.logger.info(f"正在为商品 {product.item_id} 生成文章...")
            
            # 准备商品数据
            product_data = {
                "item_id": product.item_id,
                "item_name": product.item_name,
                "desc": product.desc,
                "min_price": product.min_price,
                "max_price": product.max_price,
                "category_id": product.category_id,
                "seller_id": product.seller_id,
                "platform": product.platform
            }
            
            # 调用 AI 服务生成文章
            ai_result = self.ai_service.generate_product_article(product_data)
            
            if ai_result:
                if not ai_result.get("title"):
                    self.logger.error(f"AI 服务为商品 {product.item_id} 生成文章失败，标题为空")
                    return None
                
                if not ai_result.get("content"):
                    self.logger.error(f"AI 服务为商品 {product.item_id} 生成文章失败，内容为空")
                    return None
                # 获取本次调用所用模型名称，作为作者名存储
                model_name_used = self.ai_service.model_strategy.get_optimal_model()
                article_content = {
                    "title": ai_result.get("title", ""),
                    "content": ai_result.get("content", ""),
                    "tags": ai_result.get("tags", "商品推荐,优质好物"),
                    "author_name": model_name_used
                }
                
                self.logger.info(f"商品 {product.item_id} 文章生成成功")
                return article_content
            else:
                self.logger.error(f"AI 服务为商品 {product.item_id} 生成文章失败")
                return None
            
        except Exception as e:
            self.logger.error(f"为商品 {product.item_id} 生成文章失败: {str(e)}")
            return None
    
    def save_article_to_database(self, product: Product, article_content: dict) -> bool:
        """
        将生成的文章保存到数据库
        
        Args:
            product: 商品对象
            article_content: 文章内容字典
            
        Returns:
            是否保存成功
        """
        try:
            with Session(engine) as session:
                # 创建文章记录
                article = ProductArticle(
                    item_id=product.item_id,
                    sku_id=product.first_sku_id,
                    title=article_content["title"],
                    content=article_content["content"],
                    tag_ids="",  # 保留原字段，暂时为空
                    tags=article_content.get("tags", ""),  # 使用新的tags字段存储AI生成的标签
                    owner_id="system",  # 系统生成
                    author_name=article_content.get("author_name", "AI助手"),
                    status=ArticleStatus.DRAFT  # 设置为草稿状态
                )
                
                session.add(article)
                session.commit()
                session.refresh(article)
                
                self.logger.info(f"文章已保存到数据库，ID: {article.id}, 商品: {product.item_id}")
                return True
                
        except Exception as e:
            self.logger.error(f"保存文章到数据库失败: {str(e)}")
            return False
    
    def process_single_product(self, product: Product) -> bool:
        """
        处理单个商品，生成并保存文章
        
        Args:
            product: 商品对象
            
        Returns:
            是否处理成功
        """
        try:
            self.processed_count += 1
            
            # 生成文章内容
            article_content = self.generate_article_with_ai(product)
            if not article_content:
                self.error_count += 1
                return False
            
            # 保存到数据库
            if self.save_article_to_database(product, article_content):
                self.generated_count += 1
                return True
            else:
                self.error_count += 1
                return False
                
        except Exception as e:
            self.logger.error(f"处理商品 {product.item_id} 失败: {str(e)}")
            self.error_count += 1
            return False
    
    def run_generation_task(self):
        """执行文章生成任务"""
        start_time = time.time()
        self.logger.info("开始执行商品文章生成任务")
        
        try:
            with Session(engine) as session:
                # 获取发布配置
                config = session.exec(select(PublishConfig)).first()
                if not config or not config.is_enabled:
                    self.logger.info("发布配置未启用，跳过文章生成")
                    return
                
                # 重置计数器
                self.processed_count = 0
                self.generated_count = 0
                self.error_count = 0
                
                # 获取需要生成文章的商品
                products = self.get_products_needing_articles()
                
                if not products:
                    self.logger.info("没有需要生成文章的商品")
                    return
                
                # 计算发布时间点
                publish_times = config.calculate_publish_times(len(products))
                
                # 处理每个商品
                for product, publish_time in zip(products, publish_times):
                    article_content = self.generate_article_with_ai(product)
                    if not article_content:
                        self.error_count += 1
                        continue
                    
                    # 设置预发布时间
                    article_content["pre_publish_time"] = int(publish_time.timestamp())
                    
                    # 保存到数据库
                    if self.save_article_to_database(product, article_content):
                        self.generated_count += 1
                    else:
                        self.error_count += 1
                    
                    # 添加短暂延迟，避免过于频繁的数据库操作
                    time.sleep(1)
                
                # 统计结果
                elapsed_time = time.time() - start_time
                self.logger.info(
                    f"任务执行完成 - 处理: {self.processed_count}, "
                    f"成功: {self.generated_count}, "
                    f"失败: {self.error_count}, "
                    f"耗时: {elapsed_time:.2f}秒"
                )
                
        except Exception as e:
            self.logger.error(f"执行文章生成任务失败: {str(e)}\n{traceback.format_exc()}")


def main():
    """主函数 - 设置定时任务"""
    try:
        base_logger.info("启动商品文章生成定时任务")
        
        # 创建文章生成器
        generator = ProductArticleGenerator(logger=base_logger)
        
        # 创建任务调度器
        scheduler = TaskScheduler(timezone='Asia/Shanghai', logger=base_logger)
        
        # 添加每分钟执行的任务
        scheduler.add_minute_task(generator.run_generation_task)
        
        # 启动调度器
        base_logger.info("定时任务已启动，每分钟执行一次文章生成")
        scheduler.start()
        
    except KeyboardInterrupt:
        base_logger.info("收到中断信号，正在停止定时任务...")
    except Exception as e:
        error_msg = f"定时任务启动失败: {str(e)}\n{traceback.format_exc()}"
        base_logger.error(error_msg)
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        error_msg = f"Main function failed: {str(e)}\n{traceback.format_exc()}"
        base_logger.error(error_msg)
        sys.exit(1) 