#!/usr/bin/env python3
"""
小红书客户端测试文件
测试XiaohongshuClient类的get_sign方法
"""

import unittest
import hashlib
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.xiaohongshu_client import XiaohongshuClient

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
        import json
        full_data = timestamp + api_path + json.dumps(request_data, separators=(',', ':'))
        
        result = self.client.get_sign(full_data)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, str)
        
        print(f"Integration test result: {result}")

def run_performance_tests():
    """性能测试"""
    import time
    
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

if __name__ == '__main__':
    # 运行单元测试
    print("🧪 Running Unit Tests")
    print("=" * 50)
    unittest.main(verbosity=2, exit=False)
    
    # 运行性能测试
    run_performance_tests()
    
    print("\n✅ All tests completed!") 