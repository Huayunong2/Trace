"""
Celery configuration for elderly_tracking_system project.
"""
import os

# Celery是可选的，如果未安装则跳过
try:
    from celery import Celery
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    
    app = Celery('elderly_tracking_system')
    app.config_from_object('django.conf:settings', namespace='CELERY')
    app.autodiscover_tasks()
except ImportError:
    # Celery未安装，创建一个占位符
    app = None

