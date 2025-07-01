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
        return cls.get_default()
    
    @classmethod
    def get_default(cls) -> 'AuthConfig':
        """获取默认认证配置（用于测试）"""
        return cls(
            cookie='abRequestId=17148128-8852-551e-b570-8d9d33b75518; a1=1909140aa6868vg1i3iac08yu9pgmqivng8ems8d030000384011; webId=74294265dacea72365ce5203d2a761f9; gid=yj8jy480d0I2yj8jy4800kMYKYKYhky3q30SYf88Yv7jUdq8k6A3h6888qY48yy8iff2Y2fq; customerClientId=543401388915168; x-user-id-school.xiaohongshu.com=672b51cf000000001d02e46e; x-user-id-zhaoshang.xiaohongshu.com=672b51cf000000001d02e46e; x-user-id-fuwu.xiaohongshu.com=672b51cf000000001d02e46e; omikuji_worker_plugin_uuid=b9e544d6852e4dcc9a6602846e719e97; JSESSIONID=276FC85C2A6C1072A05DD7C7BD6B9B60; webBuild=4.68.0; web_session=030037a1b8c1d9090a45bea73a2f4ac362b491; unread={%22ub%22:%22683fdf55000000002102db0c%22%2C%22ue%22:%22681f2220000000000303eaa2%22%2C%22uc%22:23}; x-user-id-ad-market.xiaohongshu.com=672b51cf000000001d02e46e; access-token-ad-market.xiaohongshu.com=customer.ad_market.AT-68c517520597252994101402g6tud2f2gqilksyv; access-token-fuwu.xiaohongshu.com=customer.fuwu.AT-68c517521074234882182182d6lgvn2xeojquzas; access-token-fuwu.beta.xiaohongshu.com=customer.fuwu.AT-68c517521074234882182182d6lgvn2xeojquzas; loadts=1751276733811; access-token-ark.beta.xiaohongshu.com=; access-token=; sso-type=customer; subsystem=ark; xsecappid=sellercustomer; beaker.session.id=26eab5cc536f348fb62cea42c84f69852b497bd1gAJ9cQAoWAsAAABhcmstbGlhcy1pZHEBTlgOAAAAcmEtdXNlci1pZC1hcmtxAk5YDgAAAF9jcmVhdGlvbl90aW1lcQNHQdoYw/OT1wpYEQAAAHJhLWF1dGgtdG9rZW4tYXJrcQROWAMAAABfaWRxBVggAAAAZmMyOGFjYmE2NGVhNDU1NmJlZmE0Yzk2Njc1Y2YwMmRxBlgOAAAAX2FjY2Vzc2VkX3RpbWVxB0dB2hjD85PXCnUu; acw_tc=0a0d096b17513288650624266e0ba7cdd1e9cfe15c03eb3abfc88b7d432941; websectiga=634d3ad75ffb42a2ade2c5e1705a73c845837578aeb31ba0e442d75c648da36a; sec_poison_id=b41e3541-b4b3-4016-9153-6a3d7f938650; customer-sso-sid=68c517521900294627270050gsqvrmdyl1dgitku; x-user-id-ark.xiaohongshu.com=672b51cf000000001d02e46e; access-token-ark.xiaohongshu.com=customer.ark.AT-68c517521900298917764484mmyoe4mybrcdcdk5',
            authorization='AT-AT-68c517521900298917764484mmyoe4mybrcdcdk5'
        ) 