from datetime import datetime, time, timedelta
from typing import Optional
import sqlalchemy as sa
from sqlmodel import Field, SQLModel
import pytz
from app.models.base import BaseModel
from pydantic import field_validator

class PublishConfig(BaseModel, table=True):
    """发布配置模型"""
    __tablename__ = "publish_config"

    # 文章生成时间（每天几点生成文章）
    generate_time: time = Field(
        default=time(hour=8, minute=0),
        sa_column=sa.Column(sa.Time()),
        description="每天生成文章的时间点"
    )
    
    # 发布时段开始时间
    publish_start_time: time = Field(
        default=time(hour=9, minute=0),
        sa_column=sa.Column(sa.Time()),
        description="每天开始发布的时间"
    )
    
    # 发布时段结束时间
    publish_end_time: time = Field(
        default=time(hour=22, minute=0),
        sa_column=sa.Column(sa.Time()),
        description="每天结束发布的时间"
    )
    
    # 每天发布文章的最大数量
    daily_publish_limit: int = Field(
        default=20,
        description="每天最多发布的文章数量",
        ge=1,
        le=50
    )
    
    # 是否启用
    is_enabled: bool = Field(
        default=True,
        description="是否启用此配置"
    )
    
    @property
    def publish_duration_minutes(self) -> int:
        """获取可发布时间段的总分钟数"""
        start_minutes = self.publish_start_time.hour * 60 + self.publish_start_time.minute
        end_minutes = self.publish_end_time.hour * 60 + self.publish_end_time.minute
        
        # 处理跨天的情况
        if end_minutes <= start_minutes:
            end_minutes += 24 * 60  # 加上24小时的分钟数
            
        return end_minutes - start_minutes

    def calculate_publish_times(self, article_count: int) -> list[datetime]:
        """
        根据文章数量计算发布时间点，在发布时段内均匀分布
        
        Args:
            article_count: 需要发布的文章数量
            
        Returns:
            发布时间点列表，按时间顺序排序
        """
        # 如果文章数量超过每日限制，只处理限制内的数量
        article_count = min(article_count, self.daily_publish_limit)
        
        if article_count <= 0:
            return []
            
        # 获取今天的日期
        today = datetime.now(pytz.timezone('Asia/Shanghai')).date()
        
        # 生成发布时间点
        publish_times = []
        
        if article_count == 1:
            # 如果只有一篇文章，放在开始时间
            publish_times.append(datetime.combine(today, self.publish_start_time))
            return publish_times
            
        # 计算开始和结束时间的分钟数
        start_total_minutes = self.publish_start_time.hour * 60 + self.publish_start_time.minute
        end_total_minutes = self.publish_end_time.hour * 60 + self.publish_end_time.minute
        
        # 处理跨天的情况
        if end_total_minutes <= start_total_minutes:
            end_total_minutes += 24 * 60  # 加上24小时的分钟数
            
        # 计算时间间隔（分钟）
        total_duration = end_total_minutes - start_total_minutes
        interval_minutes = total_duration / (article_count - 1)
        
        # 生成均匀分布的时间点
        for i in range(article_count):
            minutes_to_add = round(i * interval_minutes)
            total_minutes = start_total_minutes + minutes_to_add
            
            # 处理超过24小时的情况
            if total_minutes >= 24 * 60:
                total_minutes -= 24 * 60
                # 如果跨天，使用下一天的日期
                today = today + timedelta(days=1)
                
            hour = total_minutes // 60
            minute = total_minutes % 60
            current_time = datetime.combine(today, time(hour=hour, minute=minute))
            publish_times.append(current_time)
        
        return publish_times

    @field_validator('daily_publish_limit')
    @classmethod
    def validate_daily_publish_limit(cls, v):
        if v < 1:
            raise ValueError('每日发布笔记数量必须大于0')
        if v > 50:
            raise ValueError('每日发布笔记数量不能超过50')
        return v
    
    @field_validator('publish_end_time')
    @classmethod
    def validate_publish_time(cls, v, info):
        if 'publish_start_time' in info.data and v <= info.data['publish_start_time']:
            raise ValueError('发布结束时间必须晚于开始时间')
        return v 