import os
import importlib

def load_settings():
    env = os.environ.get('SERVER_ENVIRONMENT', 'LOCAL').upper()
    if env == 'PROD':
        module_name = 'app.settings.prod'
    else:
        module_name = 'app.settings.local'
    return importlib.import_module(module_name) 