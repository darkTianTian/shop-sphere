import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class ProductAuthConfig:
    """商品API认证配置"""
    authorization: str
    x_s: str
    x_t: str
    cookie: str
    
    @classmethod
    def from_env(cls) -> Optional['ProductAuthConfig']:
        """从环境变量加载认证配置"""
        authorization = os.environ.get('PRODUCT_AUTHORIZATION')
        x_s = os.environ.get('PRODUCT_X_S')
        x_t = os.environ.get('PRODUCT_X_T')
        cookie = os.environ.get('PRODUCT_COOKIE')
        
        if authorization and x_s and x_t and cookie:
            return cls(authorization=authorization, x_s=x_s, x_t=x_t, cookie=cookie)
        return None
    
    @classmethod
    def get_default(cls) -> 'ProductAuthConfig':
        """获取默认认证配置（用于测试）"""
        return cls(
            authorization='AT-68c517501635539317564573ibxkzxcsywqwxzaq',
            x_s='OlqB1gFp1gclZjdBOjq6s6sp0YFbOgTCOYdUOgvKsgM3',
            x_t='1748021996358',
            cookie='acw_tc=0a42376617481667139967942e6237c41ee70482616d4b448efcd33c8702d7'
        ) 