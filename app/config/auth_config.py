import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class AuthConfig:
    """认证配置"""
    cookie: str
    authorization: str
    
    @classmethod
    def from_env(cls) -> Optional['AuthConfig']:
        """从环境变量加载认证配置"""
        cookie = os.environ.get('XIAOHONGSHU_COOKIE')
        authorization = os.environ.get('XIAOHONGSHU_AUTHORIZATION')
        
        if cookie and authorization:
            return cls(cookie=cookie, authorization=authorization)
        return None
    
    @classmethod
    def get_default(cls) -> 'AuthConfig':
        """获取默认认证配置（用于测试）"""
        return cls(
            cookie='abRequestId=17148128-8852-551e-b570-8d9d33b75518; a1=1909140aa6868vg1i3iac08yu9pgmqivng8ems8d030000384011; webId=74294265dacea72365ce5203d2a761f9; gid=yj8jy480d0I2yj8jy4800kMYKYKYhky3q30SYf88Yv7jUdq8k6A3h6888qY48yy8iff2Y2fq; x-user-id-ark.xiaohongshu.com=672b51cf000000001d02e46e; customerClientId=543401388915168; x-user-id-school.xiaohongshu.com=672b51cf000000001d02e46e; x-user-id-zhaoshang.xiaohongshu.com=672b51cf000000001d02e46e; x-user-id-fuwu.xiaohongshu.com=672b51cf000000001d02e46e; omikuji_worker_plugin_uuid=b9e544d6852e4dcc9a6602846e719e97; access-token-ark.xiaohongshu.com=customer.ark.AT-68c517512447999226252228dy4yonlxyhr1vlhj; access-token-open.xiaohongshu.com=customer.open.AT-68c5175124503829331068408uzkhlqtzwhadysx; access-token-open.beta.xiaohongshu.com=customer.open.AT-68c5175124503829331068408uzkhlqtzwhadysx; JSESSIONID=276FC85C2A6C1072A05DD7C7BD6B9B60; webBuild=4.68.0; web_session=030037a1b8c1d9090a45bea73a2f4ac362b491; xsecappid=xhs-pc-web; loadts=1749450002794; unread={%22ub%22:%22683fdf55000000002102db0c%22%2C%22ue%22:%22681f2220000000000303eaa2%22%2C%22uc%22:23}; websectiga=2a3d3ea002e7d92b5c9743590ebd24010cf3710ff3af8029153751e41a6af4a3; acw_tc=0a427e2f17496300859552990e7ff252e68615083e6734abbaf92b354db8ec',
            authorization='AT-68c517512447999226252228dy4yonlxyhr1vlhj'
        ) 