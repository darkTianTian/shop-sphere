import requests
import json
import logging
import hashlib
import math
import random
import time
from typing import Dict, Any, Optional
from dataclasses import dataclass
from ...config.auth_config import AuthConfig


@dataclass
class XiaohongshuConfig:
    """小红书API配置"""
    API_BASE_URL: str = "https://ark.xiaohongshu.com"
    TIMEOUT: int = 30
    MAX_RETRIES: int = 3
    USER_AGENT: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0.0.0 Safari/537.361442) NetType/WIFI Language/en"
    MIN_REQUEST_INTERVAL: float = 2.0  # 最小请求间隔（秒）
    MAX_REQUEST_INTERVAL: float = 5.0  # 最大请求间隔（秒）
    LAST_REQUEST_TIME: float = 0.0     # 上次请求时间


class XiaohongshuClient:
    """小红书API基础客户端，提供通用功能"""
    
    def __init__(self, config: Optional[XiaohongshuConfig] = None, logger: Optional[logging.Logger] = None):
        """初始化客户端
        
        Args:
            config: API配置，如果不提供则使用默认配置
            logger: 日志记录器，如果不提供则使用默认记录器
        """
        self.config = config or XiaohongshuConfig()
        self.logger = logger or logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.config.USER_AGENT
        })
        self._init_session()
    
    def _init_session(self):
        """初始化会话，设置默认请求头"""
        self.session.headers.update(self._get_default_headers())
    
    def _get_default_headers(self) -> Dict[str, str]:
        """获取默认请求头"""
        return {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'zh-CN,zh;q=0.9',
            'cache-control': 'no-cache',
            'content-type': 'application/json',
            'origin': self.config.API_BASE_URL,
            'pragma': 'no-cache',
            'priority': 'u=1, i',
            'referer': f'{self.config.API_BASE_URL}/app-item/list/shelf?from=ark-login',
            'sec-ch-ua': '"Google Chrome";v="135", "Not-A.Brand";v="8", "Chromium";v="135"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'X-B3-Traceid':  ''.join(random.choices("abcdef0123456789", k=16)),
        }
    
    def set_auth(self, auth_config: AuthConfig):
        """设置认证信息"""
        self.session.headers.update({
            'cookie': auth_config.cookie,
            'authorization': auth_config.authorization
        })
    
    def _dict_to_escaped_str(self, data: Dict) -> str:
        """将字典转换为带转义的字符串"""
        return json.dumps(data, ensure_ascii=True, separators=(',', ':'))
    
    def get_sign(self, timestamp: str, path: str, data: Dict[str, Any]) -> str:
        """生成签名
        
        Args:
            timestamp: 时间戳
            path: API路径
            data: 请求数据
            
        Returns:
            生成的签名字符串
        """
        # 构造签名字符串
        data_str = self._dict_to_escaped_str(data)
        g = 'test'
        sign_str = f"{timestamp}{g}{path}{data_str}"
        
        # 计算MD5
        b_md5 = hashlib.md5(sign_str.encode()).hexdigest()
        
        # Base64字符集
        d = "A4NjFqYu5wPHsO0XTdDgMa2r1ZQocVte9UJBvk6/7=yRnhISGKblCWi+LpfE8xzm3"
        self.logger.debug(f"Base64 charset: {d}")
        self.logger.debug(f"MD5 hash: {b_md5}")
        self.logger.debug(f"Sign string: {sign_str}")
        print(f"Base64 charset: {d}")
        print(f"MD5 hash: {b_md5}")
        print(f"Sign string: {sign_str}")
        
        # 初始化变量
        e = b_md5
        p = 0
        result = ""
        
        while p < len(e):
            g = "1|5|4|8|6|0|2|7|3"
            a, c, u, h, l, v, x, b = 0, 0, 0, 0, 0, 0, 0, ""
            
            for step in g.split("|"):
                if step == "0":
                    if not self._is_nan(u):
                        h = ((c & 15) << 2) | (u >> 6)
                    else:
                        h = ((c & 15) << 2) | (0 >> 6)
                elif step == "1":
                    if p < len(e):
                        a = self._get_char_code_at(e, p)
                        p += 1
                elif step == "2":
                    if not self._is_nan(u):
                        v = 63 & u
                    else:
                        v = 0
                elif step == "3":
                    if 'x' in locals() and 'l' in locals() and 'h' in locals() and 'v' in locals():
                        b = self._concat_chars(d, x, l, h, v)
                elif step == "4":
                    if p < len(e):
                        u = self._get_char_code_at(e, p)
                        p += 1
                    else:
                        u = float('nan')
                elif step == "5":
                    if p < len(e):
                        c = self._get_char_code_at(e, p)
                        p += 1
                    else:
                        c = float('nan')
                elif step == "6":
                    l = ((a & 3) << 4) | (c >> 4)
                elif step == "7":
                    if self._is_nan(c):
                        h = v = 64
                    elif self._is_nan(u):
                        v = 64
                elif step == "8":
                    x = a >> 2
            
            if 'b' in locals() and b:
                result += b
        
        self.logger.debug(f"Generated signature: {result}")
        print(f"Generated signature: {result}")
        return result
    
    def _get_char_code_at(self, text: str, index: int) -> int:
        """获取字符的ASCII码"""
        if index < len(text):
            return ord(text[index])
        return float('nan')
    
    def _is_nan(self, value) -> bool:
        """检查是否为NaN"""
        try:
            return math.isnan(float(value))
        except (TypeError, ValueError):
            return False
    
    def _concat_chars(self, d: str, x: int, l: int, h: int, v: int) -> str:
        """拼接字符串"""
        result = ""
        try:
            if 0 <= x < len(d):
                result += d[x]
            if 0 <= l < len(d):
                result += d[l]
            if 0 <= h < len(d):
                result += d[h]
            if 0 <= v < len(d):
                result += d[v]
        except (IndexError, TypeError):
            pass
        return result
    
    def set_sign(self, path: str, data: Dict[str, Any]):
        """设置签名"""
        timestamp = str(int(time.time() * 1000))
        self.session.headers['x-s'] = self.get_sign(timestamp, path, data)
        self.session.headers['x-t'] = timestamp

    def _prepare_request(self, path: str, data: Optional[Dict] = None, **kwargs):
        self.set_sign(path, data)
        self.set_auth(AuthConfig.from_env())

    def is_success(self, response: Dict[str, Any]) -> bool:
        """检查响应是否成功"""
        return response.get("success")
    
    def _make_request(self, method: str, path: str, api_base_url: str = "", data: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """发送HTTP请求
        
        Args:
            method: HTTP方法
            path: API路径
            data: 请求数据
            **kwargs: 其他请求参数
            
        Returns:
            API响应数据
            
        Raises:
            requests.RequestException: 请求异常
        """
        self._prepare_request(path, data, **kwargs)
        # 添加请求间隔
        current_time = time.time()
        time_since_last_request = current_time - self.config.LAST_REQUEST_TIME
        if time_since_last_request < self.config.MIN_REQUEST_INTERVAL:
            sleep_time = random.uniform(
                self.config.MIN_REQUEST_INTERVAL - time_since_last_request,
                self.config.MAX_REQUEST_INTERVAL - time_since_last_request
            )
            self.logger.info(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.config.LAST_REQUEST_TIME = time.time()
        if api_base_url:
            url = f"{api_base_url}{path}"
        else:
            url = f"{self.config.API_BASE_URL}{path}"
        self.logger.info(f"Making request to: {url} [method: {method}]")
        self.logger.info(f"Request data: {data}")
        
        # 准备请求数据
        if data:
            kwargs['data'] = json.dumps(data, separators=(',', ':'))
        
        # 创建请求对象
        req = requests.Request(
            method=method,
            url=url,
            headers=self.session.headers,
            **kwargs
        )
        
        # 准备请求
        prepped = self.session.prepare_request(req)
        
        # 确保content-type正确设置
        if data:
            prepped.headers['Content-Type'] = 'application/json'
        
        # 添加随机延迟
        time.sleep(random.uniform(0.5, 1.5))
        
        for attempt in range(self.config.MAX_RETRIES):
            try:
                self.logger.info(f"Sending {method} request to {url} (attempt {attempt + 1}/{self.config.MAX_RETRIES})")
                
                # 发送准备好的请求
                response = self.session.send(
                    prepped,
                    timeout=self.config.TIMEOUT
                )
                
                self.logger.info(f"Response status code: {response.status_code}")
                print("Response cookies:", dict(response.cookies))
                print("Response headers:", dict(response.headers))
                
                try:
                    response_data = response.json()
                    self.logger.debug(f"Response data: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
                    if self.is_success(response_data):
                        return response_data
                    else:
                        self.logger.error(f"Response data: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
                        return {"message": response_data.get("msg"), "status_code": response.status_code}
                except json.JSONDecodeError:
                    self.logger.warning(f"Failed to parse JSON response: {response.text}")
                    return {"raw_response": response.text, "status_code": response.status_code}
                    
            except requests.exceptions.Timeout:
                self.logger.warning(f"Request timeout (attempt {attempt + 1}/{self.config.MAX_RETRIES})")
                if attempt == self.config.MAX_RETRIES - 1:
                    raise
                    
            except requests.exceptions.RequestException as e:
                self.logger.error(f"Request error (attempt {attempt + 1}/{self.config.MAX_RETRIES}): {str(e)}")
                if attempt == self.config.MAX_RETRIES - 1:
                    raise
                    
        raise requests.RequestException("All retry attempts failed")
    
    def close(self):
        """关闭会话"""
        self.session.close() 