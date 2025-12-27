"""
URL configuration for elderly_tracking_system project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.http import JsonResponse

def health_check(request):
    """健康检查接口"""
    return JsonResponse({'status': 'ok', 'service': 'elderly_tracking_system'})

def root_view(request):
    """根路径视图"""
    return JsonResponse({
        'service': '防走失预警系统 API',
        'version': '1.0',
        'endpoints': {
            'health': '/health/',
            'api': {
                'auth': '/api/auth/',
                'devices': '/api/devices/',
                'locations': '/api/locations/',
                'fences': '/api/fences/',
                'alerts': '/api/alerts/'
            },
            'admin': '/admin/'
        }
    })

urlpatterns = [
    path('', root_view, name='root'),
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.users.urls')),
    path('api/devices/', include('apps.devices.urls')),
    path('api/locations/', include('apps.locations.urls')),
    path('api/fences/', include('apps.fences.urls')),
    path('api/alerts/', include('apps.alerts.urls')),
    path('api/system/', include('apps.system.urls')),
    path('health/', health_check, name='health_check'),
    # 地图可视化页面
    path('admin/locations/map/', TemplateView.as_view(template_name='admin/locations/map_view.html'), name='location_map'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
