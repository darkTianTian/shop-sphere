import requests
import json
import logging
import hashlib
import math
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class XiaohongshuConfig:
    """小红书API配置"""
    api_url: str = "https://edith.xiaohongshu.com/web_api/sns/v2/note"
    DOMAIN = "https://ark.xiaohongshu.com"
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
    
    def get_sign(self, b: str) -> str:
        """
        生成签名
        
        Args:
            b: 需要签名的字符串
            
        Returns:
            生成的签名字符串
        """
        # 使用固定的测试数据（如果需要的话）
        test_data = """1749462149435test/api/edith/product/search_item_v2{\"page_no\":1,\"page_size\":20,\"search_order\":{\"sort_field\":\"create_time\",\"order\":\"desc\"},\"search_filter\":{\"card_type\":2,\"is_channel\":false},\"search_item_detail_option\":{}}"""
        test_data = """1749578585081test/api/edith/product/search_item_v2{\"page_no\":1,\"page_size\":20,\"search_order\":{\"sort_field\":\"create_time\",\"order\":\"desc\"},\"search_filter\":{\"card_type\":2,\"is_channel\":false},\"search_item_detail_option\":{}}"""
        
        # 使用传入的参数或测试数据
        data_to_sign = b if b else test_data
        
        # 计算MD5哈希 (修复了原代码中的错误)
        b_md5 = hashlib.md5(test_data.encode()).hexdigest()
        
        print(f"md5====> {b_md5}")
        
        # TODO: 这里需要实现完整的签名算法
        # 目前只返回MD5，实际的小红书签名算法会更复杂
        s = ""
        
        # 初始化变量
        e = b_md5  # 输入数据
        # e = 'd4c3a08c8817dc80358145069e498aad'
        p = 0  # 指针位置
        result = ""  # 结果字符串
        
        # d由js中一个数组的若干元素组成，不确定是否固定
        d = "A4NjFqYu5wPHsO0XTdDgMa2r1ZQocVte9UJBvk6/7=yRnhISGKblCWi+LpfE8xzm3"
        
        while p < len(e):
            g = "1|5|4|8|6|0|2|7|3"
            m = 0
            
            # 初始化循环变量
            a, c, u, h, l, v, x, b = 0, 0, 0, 0, 0, 0, 0, ""
            
            for step in g.split("|"):
                if step == "0":
                    # h = 位运算操作
                    print(u, p, len(e), self._is_nan(u))
                    if not self._is_nan(u):
                        h = ((c & 15) << 2) |  (u >> 6)
                    else:
                        h = ((c & 15) << 2) |  (0 >> 6)
                elif step == "1":
                    # a = e[某个函数](p++)
                    if p < len(e):
                        a = self._get_char_code_at(e, p)
                        p += 1
                elif step == "2":
                    # print(a, c, u, l, v, x, b)
                    if not self._is_nan(u):
                        v = 63 & u
                    else:
                        v = 0
                elif step == "3":
                    # b = 字符串拼接操作
                    if 'x' in locals() and 'l' in locals() and 'h' in locals() and 'v' in locals():
                        b = self._concat_chars(d, x, l, h, v)
                elif step == "4":
                    # u = e[某个函数](p++)
                    if p < len(e):
                        u = self._get_char_code_at(e, p)
                        p += 1
                    else:
                        u = float('nan')
                elif step == "5":
                    # c = e[某个函数](p++)
                    if p < len(e):
                        c = self._get_char_code_at(e, p)
                        p += 1
                    else:
                        c = float('nan')
                elif step == "6":
                    # l = 位运算
                    l = ((a & 3) << 4) | (c >> 4)
                elif step == "7":
                    # 条件判断和赋值
                    if self._is_nan(c):
                        h = v = 64
                    elif self._is_nan(u):
                        v = 64
                elif step == "8":
                    # x = 位运算
                    x = self._bit_operation_8(a)
            print(a, c, u, h, l, v, x, b, p, result)
            
            # 将结果添加到字符串
            if 'b' in locals() and b:
                result += b
                
            # # 防止无限循环
            # if p > len(e):
            #     break
        print("final", result)
        return result 
    
    def _get_base64_chars(self) -> str:
        """获取Base64字符集"""
        return "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"
    
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
    
    def _dict_to_escaped_str(self, data: Dict) -> str:
        """将字典转换为带转义的字符串
        
        Args:
            data: 要转换的字典
            
        Returns:
            转换后的字符串，所有特殊字符都会被转义
        """
        return json.dumps(data, ensure_ascii=True, separators=(',', ':'))
    
    def _bit_operation_0(self, c: int, u: int) -> int:
        """case "0"的位运算操作"""
        # TODO: 具体实现需要根据原始JS代码
        # h = s[t(i._0x5e8d4a, i._0x2cd5ee)](s[t(1690, 1664)](s[t(1688, i._0x20c297)](c, 15), 2), s[t(i._0x50030e, 1838)](u, 6))
        if not self._is_nan(c) and not self._is_nan(u):
            return ((c << 15) >> 2) | (u >> 6)
        return 0
    
    def _bit_operation_6(self, a: int, c: int) -> int:
        """case "6"的位运算操作"""
        # TODO: 具体实现需要根据原始JS代码
        # l = s[t(1528, 1537)](s[t(i._0x3b0ebe, 1659)](s[t(i._0x349f5e, i._0x55dbbf)](a, 3), 4), s[t(i._0x5f57ca, 1535)](c, 4))
        if not self._is_nan(a) and not self._is_nan(c):
            return ((a << 3) >> 4) | (c >> 4)
        return 0
    
    def _bit_operation_8(self, a: int) -> int:
        """case "8"的位运算操作"""
        # TODO: 具体实现需要根据原始JS代码
        # x = s[t(i._0x5f57ca, i._0x2e99d3)](a, 2)
        if not self._is_nan(a):
            return a >> 2
        return 0
    
    def _concat_chars(self, d: str, x: int, l: int, h: int, v: int) -> str:
        """拼接字符串"""
        # TODO: 具体实现需要根据原始JS代码
        # b = s[t(i._0xaf931c, 1553)](s[t(i._0x14fd18, i._0x1ceff2)](b + d[t(i._0x221882, 1576)](x) + d[t(i._0x1be856, i._0x4c861e)](l), d[t(i._0x3af520, i._0xa15f86)](h)), d[t(1431, 1265)](v))
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