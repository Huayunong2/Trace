"""
系统管理视图
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from apps.users.models import ElderlyProfile
from apps.devices.models import Device
from apps.alerts.models import Alert
from .models import SystemConfig
from .serializers import SystemConfigSerializer

User = get_user_model()


class SystemConfigViewSet(viewsets.ModelViewSet):
    """
    系统配置管理
    只有系统管理员可以访问
    """
    serializer_class = SystemConfigSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # 只有系统管理员可以访问
        if self.request.user.role != 'system_admin':
            return SystemConfig.objects.none()
        
        queryset = SystemConfig.objects.all()
        
        # 支持按key查询
        key = self.request.query_params.get('key')
        if key:
            queryset = queryset.filter(key__icontains=key)
        
        return queryset
    
    def perform_create(self, serializer):
        # 只有系统管理员可以创建
        if self.request.user.role != 'system_admin':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('只有系统管理员可以创建配置')
        serializer.save()
    
    def perform_update(self, serializer):
        # 只有系统管理员可以更新
        if self.request.user.role != 'system_admin':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('只有系统管理员可以更新配置')
        serializer.save()
    
    def perform_destroy(self, instance):
        # 只有系统管理员可以删除
        if self.request.user.role != 'system_admin':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('只有系统管理员可以删除配置')
        instance.delete()
    
    @action(detail=False, methods=['get'])
    def public(self, request):
        """获取公开的配置（普通用户可访问）"""
        configs = SystemConfig.objects.filter(is_public=True)
        return Response(SystemConfigSerializer(configs, many=True).data)


class SystemAdminUserViewSet(viewsets.ModelViewSet):
    """
    系统管理员用户管理
    只有系统管理员可以访问
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # 只有系统管理员可以访问
        if self.request.user.role != 'system_admin':
            return User.objects.none()
        
        queryset = User.objects.all()
        
        # 支持按角色过滤
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(role=role)
        
        # 支持按用户名搜索
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(username__icontains=search)
        
        return queryset.order_by('-created_at')
    
    def get_serializer_class(self):
        from apps.users.serializers import UserSerializer
        return UserSerializer
    
    def perform_create(self, serializer):
        if self.request.user.role != 'system_admin':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('只有系统管理员可以创建用户')
        serializer.save()
    
    def perform_update(self, serializer):
        if self.request.user.role != 'system_admin':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('只有系统管理员可以更新用户')
        serializer.save()
    
    def perform_destroy(self, instance):
        if self.request.user.role != 'system_admin':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('只有系统管理员可以删除用户')
        # 不能删除自己
        if instance.id == self.request.user.id:
            from rest_framework.exceptions import ValidationError
            raise ValidationError('不能删除自己')
        instance.delete()
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """用户统计信息"""
        if request.user.role != 'system_admin':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('只有系统管理员可以查看统计信息')
        
        stats = {
            'total_users': User.objects.count(),
            'guardians': User.objects.filter(role='guardian').count(),
            'elderly': User.objects.filter(role='elderly').count(),
            'community_admins': User.objects.filter(role='community_admin').count(),
            'system_admins': User.objects.filter(role='system_admin').count(),
            'total_elderly_profiles': ElderlyProfile.objects.count(),
            'total_devices': Device.objects.count(),
            'active_devices': Device.objects.filter(is_active=True).count(),
            'total_alerts': Alert.objects.count(),
            'unhandled_alerts': Alert.objects.filter(is_handled=False).count(),
        }
        
        return Response(stats)
    
    @action(detail=True, methods=['post'])
    def change_role(self, request, pk=None):
        """修改用户角色"""
        if request.user.role != 'system_admin':
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('只有系统管理员可以修改用户角色')
        
        user = self.get_object()
        new_role = request.data.get('role')
        
        if not new_role or new_role not in [choice[0] for choice in User.ROLE_CHOICES]:
            return Response({'error': '无效的角色'}, status=status.HTTP_400_BAD_REQUEST)
        
        # 不能修改自己的角色
        if user.id == request.user.id:
            return Response({'error': '不能修改自己的角色'}, status=status.HTTP_400_BAD_REQUEST)
        
        user.role = new_role
        user.save()
        
        from apps.users.serializers import UserSerializer
        return Response(UserSerializer(user).data)

