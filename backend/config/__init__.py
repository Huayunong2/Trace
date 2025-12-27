# Celery是可选的，如果未安装则跳过
try:
    from .celery import app as celery_app
    __all__ = ('celery_app',)
except ImportError:
    # Celery未安装，跳过
    celery_app = None
    __all__ = ()

