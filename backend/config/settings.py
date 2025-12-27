"""
Django settings for elderly_tracking_system project.
"""
import os
from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Security settings
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-this-in-production')
DEBUG = config('DEBUG', default=True, cast=bool)
ALLOWED_HOSTS_BASE = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=lambda v: [s.strip() for s in v.split(',')])
ALLOWED_HOSTS = ALLOWED_HOSTS_BASE.copy()

# 允许所有ngrok域名（开发环境）
# Django的ALLOWED_HOSTS不支持通配符，所以我们需要添加具体的ngrok域名
# 或者使用中间件来动态允许
import re
if DEBUG:
    # 添加ngrok域名模式匹配的中间件
    pass  # 将通过中间件处理

# Application definition
INSTALLED_APPS = [
    'admin_interface',
    'colorfield',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'django_filters',
    'apps.users',
    'apps.devices',
    'apps.locations',
    'apps.fences',
    'apps.alerts',
    'apps.system',
]

MIDDLEWARE = [
    'config.middleware.AllowNgrokHostMiddleware',  # 允许ngrok域名（必须在SecurityMiddleware之前）
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
# 使用PyMySQL替代mysqlclient（Windows兼容性更好）
USE_SQLITE = config('USE_SQLITE', default=False, cast=bool)

if USE_SQLITE:
    # 使用SQLite数据库（开发环境或MySQL不可用时）
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    # 使用MySQL数据库
    try:
        import pymysql
        pymysql.install_as_MySQLdb()
    except ImportError:
        pass
    
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': config('DB_NAME', default='elderly_tracking'),
            'USER': config('DB_USER', default='root'),
            'PASSWORD': config('DB_PASSWORD', default=''),
            'HOST': config('DB_HOST', default='localhost'),
            'PORT': config('DB_PORT', default='3306'),
            'OPTIONS': {
                'charset': 'utf8mb4',
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES', time_zone='+08:00'",
            },
        }
    }

# Redis配置（如果Redis未运行，使用数据库缓存）
REDIS_AVAILABLE = False
try:
    import redis
    try:
        r = redis.Redis(host='127.0.0.1', port=6379, db=1, socket_connect_timeout=0.1, socket_timeout=0.1)
        r.ping()
        REDIS_AVAILABLE = True
    except (redis.ConnectionError, redis.TimeoutError, Exception):
        REDIS_AVAILABLE = False
except ImportError:
    # redis模块未安装
    REDIS_AVAILABLE = False

if REDIS_AVAILABLE:
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': config('REDIS_URL', default='redis://127.0.0.1:6379/1'),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            }
        }
    }
    # Redis作为会话存储
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    SESSION_CACHE_ALIAS = 'default'
else:
    # 使用数据库缓存（Redis不可用时）
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
            'LOCATION': 'cache_table',
        }
    }
    # 使用数据库会话存储
    SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = False  # 禁用时区支持，避免MySQL时区表问题

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 自定义用户模型
AUTH_USER_MODEL = 'users.User'

# REST Framework配置
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'apps.users.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

# CORS配置（允许微信小程序跨域）
if DEBUG:
    # 开发环境允许所有来源
    CORS_ALLOW_ALL_ORIGINS = True
else:
    # 生产环境只允许微信小程序域名
    CORS_ALLOWED_ORIGINS = [
        "https://servicewechat.com",
    ]
    CORS_ALLOW_CREDENTIALS = True

# JWT配置
JWT_SECRET_KEY = config('JWT_SECRET_KEY', default=SECRET_KEY)
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_DELTA = 7 * 24 * 60 * 60  # 7天

# 高德地图API配置
AMAP_KEY = config('AMAP_KEY', default='')
AMAP_SECRET = config('AMAP_SECRET', default='')

# 微信小程序配置
WECHAT_APPID = config('WECHAT_APPID', default='')
WECHAT_SECRET = config('WECHAT_SECRET', default='')

# 超级管理员openid列表（允许切换角色，用于测试）
# 格式：以逗号分隔的openid列表，例如：'openid1,openid2,openid3'
SUPER_ADMIN_OPENIDS = config('SUPER_ADMIN_OPENIDS', default='', cast=lambda v: [s.strip() for s in v.split(',') if s.strip()])

# Celery配置
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://127.0.0.1:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE

# 系统配置
LOCATION_UPDATE_INTERVAL = 30  # 定位更新间隔（秒）
FENCE_VIOLATION_THRESHOLD = 1  # 围栏越界触发次数（1表示首次越界即报警）
DEVICE_OFFLINE_THRESHOLD = 30 * 60  # 设备离线阈值（秒）
DEVICE_LOW_BATTERY_THRESHOLD = 20  # 低电量阈值（%）
ALERT_ESCALATION_TIME = 5 * 60  # 预警升级时间（秒）
TRACK_HISTORY_DAYS = 30  # 轨迹保存天数

# 微信订阅消息模板ID配置
# 注意：需要在微信公众平台配置这些模板，并获取实际的模板ID
WECHAT_SUBSCRIBE_TEMPLATES = {
    'fence_violation': config('WECHAT_TEMPLATE_FENCE_VIOLATION', default='vwOW-gQe_HZOxvu7cjduB8ZMjQEPLpwu2w6FgNSzhSg'),  # 围栏越界模板ID
    'device_offline': config('WECHAT_TEMPLATE_DEVICE_OFFLINE', default='6dVj7hpIRDy_zTaOMjPEvAdcwR3nIKcRMMZ-JFxFl9M'),  # 设备离线模板ID（使用设备状态异常通知模板）
    'low_battery': config('WECHAT_TEMPLATE_LOW_BATTERY', default='6dVj7hpIRDy_zTaOMjPEvAdcwR3nIKcRMMZ-JFxFl9M'),  # 低电量模板ID（使用设备状态异常通知模板）
    'sos': config('WECHAT_TEMPLATE_SOS', default='hU3HDKaWcVL4P8HbntKk5DbgDlV9gW-6f_-w4k8yY7o'),  # SOS求救模板ID
}

# 创建日志目录
log_dir = os.path.join(BASE_DIR, 'logs')
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# 日志配置
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs', 'django.log'),
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}

