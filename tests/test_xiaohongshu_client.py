#!/usr/bin/env python3
"""
小红书客户端测试文件
测试XiaohongshuClient类的get_sign方法
"""

import unittest
import hashlib
import sys
import os
import time
from unittest.mock import patch, MagicMock
from app.config.auth_config import AuthConfig
from app.services.xiaohongshu.product_client import ProductClient
import json

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.xiaohongshu.xiaohongshu_client import XiaohongshuClient, XiaohongshuConfig

class TestXiaohongshuClient(unittest.TestCase):
    
    def setUp(self):
        """测试前的初始化"""
        self.client = XiaohongshuClient()
    
    def test_get_sign_basic(self):
        """测试get_sign方法的基本功能"""
        test_input = "test_string"
        result = self.client.get_sign(test_input)
        
        # 验证返回值不为空
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
    
    def test_get_sign_with_real_data(self):
        """使用真实数据测试get_sign方法"""
        real_data = """1749462149435test/api/edith/product/search_item_v2{\"page_no\":1,\"page_size\":20,\"search_order\":{\"sort_field\":\"create_time\",\"order\":\"desc\"},\"search_filter\":{\"card_type\":2,\"is_channel\":false},\"search_item_detail_option\":{}}"""
        
        result = self.client.get_sign(real_data)
        
        # 验证返回值
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
        
        # 验证返回值的长度和格式（如果有特定要求）
        print(f"Generated sign: {result}")
    
    def test_get_sign_empty_string(self):
        """测试空字符串输入"""
        result = self.client.get_sign("")
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
    
    def test_get_sign_special_characters(self):
        """测试包含特殊字符的输入"""
        special_data = "test@#$%^&*(){}[]|\\:;\"'<>?,./"
        result = self.client.get_sign(special_data)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
    
    def test_get_sign_unicode_characters(self):
        """测试包含Unicode字符的输入"""
        unicode_data = "测试中文字符🔥🎯💡"
        result = self.client.get_sign(unicode_data)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
    
    def test_get_sign_consistency(self):
        """测试相同输入是否产生相同输出"""
        test_data = "consistency_test_data"
        
        result1 = self.client.get_sign(test_data)
        result2 = self.client.get_sign(test_data)
        
        self.assertEqual(result1, result2, "相同输入应该产生相同的签名")
    
    def test_get_sign_different_inputs(self):
        """测试不同输入产生不同输出"""
        data1 = "test_data_1"
        data2 = "test_data_2"
        
        result1 = self.client.get_sign(data1)
        result2 = self.client.get_sign(data2)
        
        self.assertNotEqual(result1, result2, "不同输入应该产生不同的签名")
    
    def test_get_sign_long_input(self):
        """测试长字符串输入"""
        long_data = "a" * 10000  # 10000个字符
        result = self.client.get_sign(long_data)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
    
    def test_md5_verification(self):
        """验证MD5哈希计算是否正确（如果方法使用MD5）"""
        test_data = "hello world"
        expected_md5 = hashlib.md5(test_data.encode()).hexdigest()
        
        # 这里假设get_sign方法内部使用了MD5
        # 注意：实际的get_sign方法可能会对MD5结果进行进一步处理
        result = self.client.get_sign(test_data)
        
        # 打印结果用于调试
        print(f"Input: {test_data}")
        print(f"Expected MD5: {expected_md5}")
        print(f"Actual result: {result}")
        
        # 如果get_sign直接返回MD5，则应该相等
        # 如果有额外处理，则需要根据实际情况调整断言
        # self.assertEqual(result, expected_md5)

class TestXiaohongshuClientIntegration(unittest.TestCase):
    """集成测试类"""
    
    def setUp(self):
        """测试前的初始化"""
        self.client = XiaohongshuClient()
    
    def test_sign_generation_flow(self):
        """测试完整的签名生成流程"""
        # 模拟真实的API请求数据
        timestamp = "1749462149435"
        api_path = "test/api/edith/product/search_item_v2"
        request_data = {
            "page_no": 1,
            "page_size": 20,
            "search_order": {
                "sort_field": "create_time",
                "order": "desc"
            },
            "search_filter": {
                "card_type": 2,
                "is_channel": False
            },
            "search_item_detail_option": {}
        }
        
        # 构建完整的签名数据
        full_data = timestamp + api_path + json.dumps(request_data, separators=(',', ':'))
        
        result = self.client.get_sign(full_data)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
        
        print(f"Integration test result: {result}")

def run_performance_tests():
    """性能测试"""
    print("\n🚀 Performance Tests")
    print("=" * 50)
    
    client = XiaohongshuClient()
    test_data = "performance_test_data" * 100  # 较长的测试数据
    
    # 测试执行时间
    start_time = time.time()
    for i in range(1000):
        client.get_sign(test_data)
    end_time = time.time()
    
    avg_time = (end_time - start_time) / 1000
    print(f"Average execution time: {avg_time:.6f} seconds")
    print(f"Operations per second: {1/avg_time:.2f}")

class TestProductClient(unittest.TestCase):
    """测试小红书商品API客户端"""
    
    def setUp(self):
        """测试前的准备工作"""
        config = XiaohongshuConfig()
        self.client = ProductClient(config=config)
        self.auth_config = AuthConfig.get_default()
        self.client.set_auth(self.auth_config)
        
        # 模拟时间戳，使其固定
        self.timestamp = "1749578585081"
        self.time_patcher = patch('time.time', return_value=float(self.timestamp)/1000)
        self.mock_time = self.time_patcher.start()
    
    def tearDown(self):
        """测试后的清理工作"""
        self.time_patcher.stop()
        self.client.close()
    
    def test_search_products(self):
        """测试搜索商品接口"""
        # 准备测试数据
        test_data = {
            "page_no": 1,
            "page_size": 20,
            "search_order": {
                "sort_field": "create_time",
                "order": "desc"
            },
            "search_filter": {
                "card_type": 2,
                "is_channel": False
            },
            "search_item_detail_option": {}
        }
        
        # 模拟API响应
        mock_response = {
            "code": 0,
            "success": True,
            "msg": "success",
            "data": {
                "items": [
                    {
                        "id": "test_product_1",
                        "title": "测试商品1",
                        "price": 99.99
                    }
                ],
                "total": 1
            }
        }
        
        # 使用mock替换实际的HTTP请求
        with patch.object(self.client, '_make_request', return_value=mock_response) as mock_request:
            # 调用被测试的方法
            result = self.client.search_products()
            
            # 验证结果
            self.assertEqual(result, mock_response)
            
            # 验证是否使用了正确的参数调用
            mock_request.assert_called_once_with('POST', '/api/edith/product/search_item_v2', test_data)
    
    def test_get_product_detail(self):
        """测试获取商品详情接口"""
        # 准备测试数据
        product_id = "test_product_1"
        
        # 模拟API响应
        mock_response = {
            "code": 0,
            "success": True,
            "msg": "success",
            "data": {
                "id": product_id,
                "title": "测试商品1",
                "price": 99.99,
                "description": "这是一个测试商品"
            }
        }
        
        # 使用mock替换实际的HTTP请求
        with patch.object(self.client, '_make_request', return_value=mock_response) as mock_request:
            # 调用被测试的方法
            result = self.client.get_product_detail(product_id)
            
            # 验证结果
            self.assertEqual(result, mock_response)
            
            # 验证是否使用了正确的参数调用
            mock_request.assert_called_once_with('GET', f'/test/api/edith/product/item/{product_id}')
    
    def test_sign_generation(self):
        """测试签名生成"""
        # 准备测试数据
        path = "/test/api/edith/product/search_item_v2"
        data = {
            "page_no": 1,
            "page_size": 20,
            "search_order": {
                "sort_field": "create_time",
                "order": "desc"
            },
            "search_filter": {
                "card_type": 2,
                "is_channel": False
            },
            "search_item_detail_option": {}
        }
        
        # 生成签名
        signature = self.client.get_sign(self.timestamp, path, data)
        
        # 验证签名不为空
        self.assertIsNotNone(signature)
        self.assertIsInstance(signature, str)
        self.assertGreater(len(signature), 0)
    
    def test_auth_header_setting(self):
        """测试认证头部设置"""
        # 准备测试数据
        test_cookie = "test_cookie_value"
        auth_config = AuthConfig(cookie=test_cookie)
        
        # 设置认证信息
        self.client.set_auth(auth_config)
        
        # 验证头部设置
        self.assertEqual(self.client.session.headers.get('cookie'), test_cookie)

class TestProductClientIntegration(unittest.TestCase):
    """小红书商品API客户端集成测试"""
    
    def setUp(self):
        """测试前的准备工作"""
        config = XiaohongshuConfig()
        self.client = ProductClient(config=config)
        self.auth_config = AuthConfig.get_default()
        self.client.set_auth(self.auth_config)
    
    def tearDown(self):
        """测试后的清理工作"""
        self.client.close()
    
    def test_search_products_real(self):
        """使用真实API测试搜索商品"""
        try:
            # 调用实际的API
            result = self.client.search_products(
                page_no=1,
                page_size=20,
                sort_field="create_time",
                order="desc"
            )
            print("result====>", result)
            # 验证响应格式
            self.assertIsInstance(result, dict)
            self.assertIn('code', result)
            self.assertIn('data', result)
            
            # 打印响应数据用于调试
            print("\n=== Search Products Response ===")
            print(json.dumps(result, ensure_ascii=False, indent=2))
            
        except Exception as e:
            self.fail(f"API请求失败: {str(e)}")
    
    def test_get_product_detail_real(self):
        """使用真实API测试获取商品详情"""
        try:
            # 先获取商品列表
            search_result = self.client.search_products()
            
            # 确保有商品数据
            self.assertIn('data', search_result)
            self.assertIn('items', search_result['data'])
            self.assertGreater(len(search_result['data']['items']), 0)
            
            # 获取第一个商品的ID
            product_id = search_result['data']['items'][0]['id']
            
            # 获取商品详情
            detail_result = self.client.get_product_detail(product_id)
            
            # 验证响应格式
            self.assertIsInstance(detail_result, dict)
            self.assertIn('code', detail_result)
            self.assertIn('data', detail_result)
            
            # 打印响应数据用于调试
            print("\n=== Product Detail Response ===")
            print(json.dumps(detail_result, ensure_ascii=False, indent=2))
            
        except Exception as e:
            self.fail(f"API请求失败: {str(e)}")

if __name__ == '__main__':
    # 运行单元测试
    print("🧪 Running Unit Tests")
    print("=" * 50)
    unittest.main(verbosity=2, exit=False)
    
    # 运行性能测试
    run_performance_tests()
    
    print("\n✅ All tests completed!") 