import requests
import json
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class XiaohongshuConfig:
    """小红书API配置"""
    api_url: str = "https://edith.xiaohongshu.com/web_api/sns/v2/note"
    timeout: int = 30
    max_retries: int = 3


class XiaohongshuClient:
    """小红书API客户端"""
    
    def __init__(self, config: Optional[XiaohongshuConfig] = None, logger: Optional[logging.Logger] = None):
        self.config = config or XiaohongshuConfig()
        self.logger = logger or logging.getLogger(__name__)
        self.session = requests.Session()
        
    def _get_default_headers(self) -> Dict[str, str]:
        """获取默认请求头"""
        return {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'zh-CN,zh;q=0.9',
            'cache-control': 'no-cache',
            'content-type': 'application/json',
            'origin': 'https://ark.xiaohongshu.com',
            'pragma': 'no-cache',
            'priority': 'u=1, i',
            'referer': 'https://ark.xiaohongshu.com/',
            'sec-ch-ua': '"Google Chrome";v="131", "Chromium";v="131", "Not_A Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'
        }
    
    def set_auth_headers(self, cookie: str, x_s: str, x_t: str):
        """设置认证相关的请求头"""
        auth_headers = {
            'cookie': cookie,
            'x-s': x_s,
            'x-t': x_t
        }
        self.session.headers.update(auth_headers)
        
    def send_note(self, note_data: Dict[str, Any], custom_headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        发送笔记到小红书
        
        Args:
            note_data: 笔记数据
            custom_headers: 自定义请求头
            
        Returns:
            API响应数据
            
        Raises:
            requests.RequestException: 请求异常
        """
        headers = self._get_default_headers()
        if custom_headers:
            headers.update(custom_headers)
            
        payload = json.dumps(note_data, ensure_ascii=False)
        
        for attempt in range(self.config.max_retries):
            try:
                self.logger.info(f"发送笔记请求 (尝试 {attempt + 1}/{self.config.max_retries})")
                
                response = self.session.post(
                    self.config.api_url,
                    headers=headers,
                    data=payload,
                    timeout=self.config.timeout
                )
                
                # 记录响应状态
                self.logger.info(f"响应状态码: {response.status_code}")
                
                # 尝试解析JSON响应
                try:
                    response_data = response.json()
                    self.logger.info(f"响应数据: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
                    return response_data
                except json.JSONDecodeError:
                    self.logger.warning(f"无法解析JSON响应，原始响应: {response.text}")
                    return {"raw_response": response.text, "status_code": response.status_code}
                    
            except requests.exceptions.Timeout:
                self.logger.warning(f"请求超时 (尝试 {attempt + 1}/{self.config.max_retries})")
                if attempt == self.config.max_retries - 1:
                    raise
                    
            except requests.exceptions.RequestException as e:
                self.logger.error(f"请求异常 (尝试 {attempt + 1}/{self.config.max_retries}): {str(e)}")
                if attempt == self.config.max_retries - 1:
                    raise
                    
        raise requests.RequestException("所有重试尝试都失败了")
    
    def close(self):
        """关闭会话"""
        self.session.close() 