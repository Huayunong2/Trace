"""
生产环境配置文件
继承自settings.py，覆盖生产环境特定配置
"""
from .settings import *
import os

# 强制关闭DEBUG
DEBUG = False

# 移除ngrok中间件（生产环境不需要）
if 'config.middleware.AllowNgrokHostMiddleware' in MIDDLEWARE:
    MIDDLEWARE.remove('config.middleware.AllowNgrokHostMiddleware')

# 安全设置
SECURE_SSL_REDIRECT = True  # 强制HTTPS
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# 必须配置的ALLOWED_HOSTS
# 在生产环境需要设置为实际域名
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='', cast=lambda v: [s.strip() for s in v.split(',') if s.strip()])

# 如果ALLOWED_HOSTS为空，抛出错误
if not ALLOWED_HOSTS:
    raise ValueError('生产环境必须配置ALLOWED_HOSTS环境变量')

# 必须配置SECRET_KEY
if SECRET_KEY == 'django-insecure-change-this-in-production':
    raise ValueError('生产环境必须配置强SECRET_KEY，不能使用默认值')

# 必须配置JWT_SECRET_KEY
if JWT_SECRET_KEY == SECRET_KEY:
    JWT_SECRET_KEY = config('JWT_SECRET_KEY', default=None)
    if not JWT_SECRET_KEY:
        raise ValueError('生产环境建议配置独立的JWT_SECRET_KEY')

# 必须使用MySQL，不允许SQLite
if USE_SQLITE:
    raise ValueError('生产环境不允许使用SQLite，必须使用MySQL')

# 必须配置微信小程序AppID和Secret
if not WECHAT_APPID or not WECHAT_SECRET:
    raise ValueError('生产环境必须配置WECHAT_APPID和WECHAT_SECRET')

# CSRF信任域名（必须配置实际域名）
CSRF_TRUSTED_ORIGINS = [f'https://{host}' for host in ALLOWED_HOSTS]

# 日志配置（生产环境更详细）
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'error.log'),
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['file', 'error_file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'error_file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

