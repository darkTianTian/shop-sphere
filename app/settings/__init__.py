import os
import importlib

def load_settings():
    """加载配置
    根据环境变量加载不同的配置类
    """
    env = os.environ.get('SERVER_ENVIRONMENT', 'LOCAL').upper()
    if env == 'PROD':
        from app.settings.prod import Settings
    else:
        from app.settings.local import Settings
    return Settings() 