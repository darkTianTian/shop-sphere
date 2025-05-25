import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class AuthConfig:
    """认证配置"""
    cookie: str
    x_s: str
    x_t: str
    
    @classmethod
    def from_env(cls) -> Optional['AuthConfig']:
        """从环境变量加载认证配置"""
        cookie = os.environ.get('XIAOHONGSHU_COOKIE')
        x_s = os.environ.get('XIAOHONGSHU_X_S')
        x_t = os.environ.get('XIAOHONGSHU_X_T')
        
        if cookie and x_s and x_t:
            return cls(cookie=cookie, x_s=x_s, x_t=x_t)
        return None
    
    @classmethod
    def get_default(cls) -> 'AuthConfig':
        """获取默认认证配置（用于测试）"""
        return cls(
            cookie='abRequestId=17148128-8852-551e-b570-8d9d33b75518; a1=1909140aa6868vg1i3iac08yu9pgmqivng8ems8d030000384011; webId=74294265dacea72365ce5203d2a761f9; gid=yj8jy480d0I2yj8jy4800kMYKYKYhky3q30SYf88Yv7jUdq8k6A3h6888qY48yy8iff2Y2fq; x-user-id-ark.xiaohongshu.com=672b51cf000000001d02e46e; customerClientId=543401388915168; x-user-id-school.xiaohongshu.com=672b51cf000000001d02e46e; x-user-id-zhaoshang.xiaohongshu.com=672b51cf000000001d02e46e; access-token-ark.xiaohongshu.com=customer.ark.AT-68c517444573634391298590bguwrrd7kl8v7n6q; x-user-id-fuwu.xiaohongshu.com=672b51cf000000001d02e46e; access-token-fuwu.xiaohongshu.com=customer.fuwu.AT-68c5174445810904503743591hyqvc0hh6ot1zle; access-token-fuwu.beta.xiaohongshu.com=customer.fuwu.AT-68c5174445810904503743591hyqvc0hh6ot1zle; webBuild=4.46.0; xsecappid=xhs-pc-web; websectiga=8886be45f388a1ee7bf611a69f3e174cae48f1ea02c0f8ec3256031b8be9c7ee; web_session=040069b65f128724b438f2b562354b88c7f94a; acw_tc=0a0b122517339037034678958eb92a1913646b1dfb3d4f32a476bc12ae225d',
            x_s='slA+ZBTbO6dJ0g1L1l5Ks6ZB12qBsg9iOl4UZYa61ls3',
            x_t='1733904910874'
        ) 