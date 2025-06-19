"""
AI 提示词模型
用于存储和管理各种 AI 生成任务的提示词模板
"""

from datetime import datetime
from typing import Optional
from pydantic import Field
from enum import Enum
import sqlalchemy as sa
from app.models.base import BaseModel

class PromptType(str, Enum):
    """提示词类型枚举"""
    PRODUCT_ARTICLE = "product_article"  # 商品文章生成


class AIPromptTemplate(BaseModel, table=True):
    """AI 提示词模板表"""
    
    __tablename__ = "ai_prompt_templates"
    
    name: str = Field(max_length=100, description="提示词模板名称")
    prompt_type: PromptType = Field(description="提示词类型")
    prompt_template: str = Field(description="提示词模板内容，支持变量占位符", sa_type=sa.String(length=4096))
    is_active: bool = Field(default=True, description="是否启用")
    platform: str = Field(max_length=20, description="平台")
    created_by: str = Field(max_length=50, description="创建者")
    owner_id: str = Field(max_length=50, description="所有者ID")
    
    class Config:
        """配置类"""
        use_enum_values = True  # 使用枚举值而不是枚举对象 