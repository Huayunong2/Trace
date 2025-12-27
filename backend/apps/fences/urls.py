"""
围栏路由
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FenceViewSet, FenceViolationLogViewSet

router = DefaultRouter()
router.register(r'', FenceViewSet, basename='fence')
router.register(r'violations', FenceViolationLogViewSet, basename='fence-violation')

urlpatterns = [
    path('', include(router.urls)),
]

