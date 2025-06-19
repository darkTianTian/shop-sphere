"""
AI 服务模块
提供与各种 AI 服务的集成，包括 DeepSeek AI
"""

import os
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

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
            self.logger.warning("DeepSeek AI 未配置，将使用模拟数据")
    
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
                return self._generate_mock_article(product_data)
            
            # TODO: 实现真实的 DeepSeek AI 调用
            return self._call_deepseek_api(product_data)
            
        except Exception as e:
            self.logger.error(f"生成文章失败: {str(e)}")
            # 降级到模拟数据
            return self._generate_mock_article(product_data)
    
    def _call_deepseek_api(self, product_data: Dict[str, Any]) -> Optional[Dict[str, str]]:
        """
        调用 DeepSeek AI API 生成文章
        
        Args:
            product_data: 商品数据
            
        Returns:
            生成的文章内容
        """
        try:
            # TODO: 实现真实的 API 调用
            # 示例代码结构：
            
            # 构建提示词
            prompt = self._build_article_prompt(product_data)
            
            # 调用 AI API（需要实际实现）
            # response = deepseek.complete(
            #     prompt=prompt,
            #     max_tokens=2000,
            #     temperature=0.7
            # )
            
            # 解析响应
            # article_content = self._parse_ai_response(response)
            
            # 暂时返回模拟数据
            self.logger.info("DeepSeek AI API 调用功能待实现")
            return self._generate_mock_article(product_data)
            
        except Exception as e:
            self.logger.error(f"调用 DeepSeek AI API 失败: {str(e)}")
            return None
    
    def _build_article_prompt(self, product_data: Dict[str, Any]) -> str:
        """
        构建文章生成的提示词
        
        Args:
            product_data: 商品数据
            
        Returns:
            提示词字符串
        """
        item_name = product_data.get('item_name', '商品')
        description = product_data.get('desc', '')
        min_price = product_data.get('min_price', 0) / 100
        max_price = product_data.get('max_price', 0) / 100
        
        prompt = f"""
请为以下商品写一篇详细的介绍文章：

商品名称：{item_name}
商品描述：{description}
价格区间：¥{min_price:.2f} - ¥{max_price:.2f}

要求：
1. 文章标题要吸引人，突出商品特色
2. 内容要包含商品特点、使用场景、购买建议等
3. 语言要生动有趣，符合小红书风格
4. 字数控制在300-800字之间
5. 使用 Markdown 格式
6. 最后提供3-5个相关标签

请按以下JSON格式返回：
{{
    "title": "文章标题",
    "content": "文章内容（Markdown格式）",
    "tags": "标签1,标签2,标签3"
}}
        """.strip()
        
        return prompt
    
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
    
    def _generate_mock_article(self, product_data: Dict[str, Any]) -> Dict[str, str]:
        """
        生成模拟文章内容（用于测试和降级）
        
        Args:
            product_data: 商品数据
            
        Returns:
            模拟的文章内容
        """
        item_name = product_data.get('item_name', '优质商品')
        description = product_data.get('desc', '这是一款值得推荐的商品')
        min_price = product_data.get('min_price', 0) / 100
        max_price = product_data.get('max_price', 0) / 100
        
        # 根据商品名称生成一些简单的标签
        tags = self._generate_tags_from_name(item_name)
        
        content = f"""# {item_name} - 值得拥有的好物推荐

## 🌟 商品亮点

{description}

这款商品凭借其出色的品质和贴心的设计，赢得了众多用户的喜爱。无论是日常使用还是特殊场合，都能满足您的需求。

## 💰 价格信息

**价格区间：¥{min_price:.2f} - ¥{max_price:.2f}**

价格亲民，性价比超高！现在入手正是时候。

## 🛒 购买建议

- ✅ 适合追求品质生活的用户
- ✅ 性价比优秀，值得信赖
- ✅ 多种规格可选，满足不同需求

## 📝 小贴士

建议在购买前仔细查看商品详情，选择最适合自己的规格和型号。

---

*本文由 AI 助手自动生成，内容仅供参考。具体商品信息请以商家页面为准。*

⏰ 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

        return {
            "title": f"{item_name} - 详细评测与购买指南",
            "content": content,
            "tags": tags
        }
    
    def _generate_tags_from_name(self, item_name: str) -> str:
        """
        根据商品名称生成标签
        
        Args:
            item_name: 商品名称
            
        Returns:
            逗号分隔的标签字符串
        """
        # 简单的标签生成逻辑
        base_tags = ["好物推荐", "种草"]
        
        # 根据关键词添加特定标签
        keywords_tags = {
            "美妆": ["美妆", "护肤"],
            "服装": ["穿搭", "时尚"],
            "数码": ["数码", "科技"],
            "家居": ["家居", "生活"],
            "食品": ["美食", "零食"],
            "母婴": ["母婴", "宝宝"],
            "运动": ["运动", "健身"],
            "宠物": ["宠物", "萌宠"]
        }
        
        for keyword, tags in keywords_tags.items():
            if keyword in item_name:
                base_tags.extend(tags)
                break
        
        return ",".join(base_tags[:5])  # 最多返回5个标签 