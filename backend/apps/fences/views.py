from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.users.models import ElderlyProfile
from apps.devices.models import Device
from .models import Fence, FenceViolationLog
from .serializers import FenceSerializer, FenceCreateSerializer, FenceViolationLogSerializer


class FenceViewSet(viewsets.ModelViewSet):
    serializer_class = FenceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # 如果是老人角色，查看与自己用户直接关联的设备围栏
        if user.role == 'elderly':
            devices = Device.objects.filter(elderly__user=user)
        else:
            # 监护人角色：查看自己管理的老人设备围栏
            elderly_profiles = ElderlyProfile.objects.filter(guardian=user)
            devices = Device.objects.filter(elderly__in=elderly_profiles)
        
        # 使用select_related优化查询
        fences = Fence.objects.select_related(
            'device', 'device__elderly', 'device__elderly__guardian'
        ).filter(device__in=devices)
        
        device_id = self.request.query_params.get('device_id')
        if device_id:
            fences = fences.filter(device__device_id=device_id)
        
        return fences
    
    def get_serializer_class(self):
        return FenceCreateSerializer if self.action == 'create' else FenceSerializer
    
    @action(detail=True, methods=['post'])
    def toggle(self, request, pk=None):
        fence = self.get_object()
        fence.is_active = not fence.is_active
        fence.save()
        return Response(FenceSerializer(fence).data)


class FenceViolationLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = FenceViolationLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # 如果是老人角色，查看与自己用户直接关联的设备围栏日志
        if user.role == 'elderly':
            devices = Device.objects.filter(elderly__user=user)
        else:
            # 监护人角色：查看自己管理的老人设备围栏日志
            elderly_profiles = ElderlyProfile.objects.filter(guardian=user)
            devices = Device.objects.filter(elderly__in=elderly_profiles)
        
        fences = Fence.objects.filter(device__in=devices)
        # 使用select_related优化查询
        return FenceViolationLog.objects.select_related(
            'fence', 'fence__device', 'location'
        ).filter(fence__in=fences)

