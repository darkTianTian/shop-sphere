"""
AI 服务模块
提供与各种 AI 服务的集成，包括 DeepSeek AI
"""

import os
import json
import logging
from openai import OpenAI
from typing import Optional, Dict, Any
from datetime import datetime
from string import Template
from sqlmodel import Session, select

from app.internal.db import engine
from app.models.prompt import AIPromptTemplate, PromptType

# TODO: 添加 DeepSeek AI SDK 依赖
# import deepseek  # 实际使用时需要安装对应的 SDK


class DeepSeekConfig:
    """DeepSeek AI 配置"""
    
    @classmethod
    def get_api_key(cls) -> str:
        """获取 API Key"""
        return os.getenv('DEEPSEEK_API_KEY', '')
    
    @classmethod
    def get_base_url(cls) -> str:
        """获取 API 基础URL"""
        return os.getenv('DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
    
    @classmethod
    def is_configured(cls) -> bool:
        """检查是否已配置"""
        return bool(cls.get_api_key())


class DeepSeekAIService:
    """DeepSeek AI 服务"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.config = DeepSeekConfig
        
        if not self.config.is_configured():
            self.logger.error("DeepSeek AI 未配置，无法使用AI生成功能")
    
    def generate_product_article(self, product_data: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """
        为商品生成文章内容
        
        Args:
            product_data: 商品数据字典，包含商品信息
            
        Returns:
            包含文章内容的字典 {"title": "", "content": "", "tags": ""}
        """
        try:
            if not self.config.is_configured():
                self.logger.error("DeepSeek AI 未配置，无法生成文章")
                return None
            
            return self._call_deepseek_api(product_data)
            
        except Exception as e:
            self.logger.error(f"生成文章失败: {str(e)}")
            return None
    
    def _call_deepseek_api(self, product_data: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """
        调用 DeepSeek AI API 生成文章
        
        Args:
            product_data: 商品数据
            
        Returns:
            生成的文章内容
        """
        try:
            # 构建提示词
            prompt = self._build_article_prompt(product_data)
            if not prompt:
                self.logger.error("无法构建提示词")
                return None
                
            self.logger.info(f"调用 DeepSeek API 生成文章")
            client = OpenAI(api_key=self.config.get_api_key(), base_url=self.config.get_base_url())
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2000,
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            self.logger.info(f"response: {response}")
            
            # 解析响应
            article_content = self._parse_ai_response(response.choices[0].message.content)
            return article_content
            
        except Exception as e:
            self.logger.error(f"调用 DeepSeek AI API 失败: {str(e)}")
            return None
    
    def _get_prompt_template(self, prompt_type: PromptType) -> Optional[str]:
        """
        从数据库获取提示词模板
        
        Args:
            prompt_type: 提示词类型
            
        Returns:
            提示词模板字符串，如果没有则返回 None
        """
        try:
            with Session(engine) as session:
                query = select(AIPromptTemplate).where(
                    AIPromptTemplate.prompt_type == prompt_type,
                    AIPromptTemplate.is_active == True
                ).order_by(AIPromptTemplate.create_at.desc())
                
                template = session.exec(query).first()
                if template:
                    self.logger.info(f"使用数据库中的提示词模板: {template.name}")
                    return template.prompt_template
                
                return None
                
        except Exception as e:
            self.logger.error(f"获取提示词模板失败: {str(e)}")
            return None
    
    def _get_default_prompt_template(self, prompt_type: PromptType) -> str:
        """
        获取默认提示词模板（后备方案）
        
        Args:
            prompt_type: 提示词类型
            
        Returns:
            默认提示词模板字符串
        """
        default_templates = {
            PromptType.PRODUCT_ARTICLE: """请为以下商品写一篇小红书风格的带货文章：

            商品名称：$item_name
            商品描述：$description

            要求：
            1. 文章标题要吸引人，突出商品特色，字数严格控制在20字以内
            2. 内容要包含商品特点、使用场景
            3. 语言要生动有趣，符合小红书风格，可以适当添加emoji表情
            4. 正文字数控制在300-800字之间
            5. 最后提供3-5个相关标签

            请按以下JSON格式返回：
            {
                "title": "文章标题",
                "content": "文章内容",
                "tags": "标签1,标签2,标签3"
            }"""
                    }
        
        return default_templates.get(prompt_type, "请为商品 $item_name 生成相关内容")
    
    def _build_article_prompt(self, product_data: Dict[str, Any]) -> Optional[str]:
        """
        构建文章生成的提示词
        
        Args:
            product_data: 商品数据
            
        Returns:
            提示词字符串
        """
        try:
            # 准备变量
            variables = {
                'item_name': product_data.get('item_name', '商品'),
                'description': product_data.get('desc', ''),
            }
            
            # 尝试从数据库获取模板
            template_str = self._get_prompt_template(PromptType.PRODUCT_ARTICLE)
            
            # 如果数据库中没有模板，使用默认模板
            if not template_str:
                self.logger.info("数据库中未找到提示词模板，使用默认模板")
                template_str = self._get_default_prompt_template(PromptType.PRODUCT_ARTICLE)
            
            # 渲染模板
            template = Template(template_str)
            prompt = template.safe_substitute(variables)
            
            return prompt
            
        except Exception as e:
            self.logger.error(f"构建提示词失败: {str(e)}")
            return None
    
    def _parse_ai_response(self, response: str) -> Optional[Dict[str, str]]:
        """
        解析 AI 响应
        
        Args:
            response: AI 返回的响应
            
        Returns:
            解析后的文章内容
        """
        try:
            # 尝试解析 JSON 响应
            data = json.loads(response)
            
            return {
                "title": data.get("title", ""),
                "content": data.get("content", ""),
                "tags": data.get("tags", "")
            }
            
        except json.JSONDecodeError:
            # 如果不是 JSON 格式，尝试其他解析方式
            self.logger.warning("AI 响应不是有效的 JSON 格式")
            return None 