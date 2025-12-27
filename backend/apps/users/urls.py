"""
用户管理路由
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, ElderlyProfileViewSet, SubscribeMessageViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'elderly', ElderlyProfileViewSet, basename='elderly')
router.register(r'subscribe', SubscribeMessageViewSet, basename='subscribe')

urlpatterns = router.urls
