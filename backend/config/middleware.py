"""
自定义中间件 - 允许ngrok域名
"""
import re
from django.conf import settings


class AllowNgrokHostMiddleware:
    """
    中间件：在开发环境中允许所有ngrok域名
    必须在SecurityMiddleware之前执行，以便在ALLOWED_HOSTS检查前添加ngrok域名
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # 匹配ngrok域名模式：*.ngrok-free.dev 或 *.ngrok.io
        self.ngrok_pattern = re.compile(r'.*\.(ngrok-free\.dev|ngrok\.io)$')

    def __call__(self, request):
        # 检查Host是否为ngrok域名
        host = request.get_host().split(':')[0]  # 移除端口号
        
        # 如果是ngrok域名且不在ALLOWED_HOSTS中，则添加
        if self.ngrok_pattern.match(host) and host not in settings.ALLOWED_HOSTS:
            # 在开发环境中，动态添加ngrok域名到ALLOWED_HOSTS
            if settings.DEBUG:
                settings.ALLOWED_HOSTS = list(settings.ALLOWED_HOSTS) + [host]
        
        return self.get_response(request)

