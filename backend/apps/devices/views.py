from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db import models
from apps.users.models import ElderlyProfile
from .models import Device
from .serializers import DeviceSerializer, DeviceCreateSerializer


class DeviceViewSet(viewsets.ModelViewSet):
    serializer_class = DeviceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # 如果是老人角色，需要特殊处理
        if user.role == 'elderly':
            # 老人可以查询的设备包括：
            # 1. 绑定到自己创建的档案的设备（elderly.user = user）
            # 2. 自己创建的设备（created_by = user），即使设备被监护人绑定到其他档案
            # 注意：如果数据库还没有 created_by 字段，会回退到只使用 elderly__user 查询
            try:
                # 尝试使用包含 created_by 的完整查询，使用select_related优化
                devices = Device.objects.select_related(
                    'elderly', 'elderly__user', 'elderly__guardian', 'created_by'
                ).filter(
                    models.Q(elderly__user=user) | models.Q(created_by=user)
                ).distinct()
            except Exception:
                # 如果查询失败（数据库字段可能不存在），回退到只使用 elderly__user
                devices = Device.objects.select_related(
                    'elderly', 'elderly__user', 'elderly__guardian'
                ).filter(elderly__user=user)
        else:
            # 监护人角色：查看自己管理的老人设备（elderly.guardian = user）
            elderly_profiles = ElderlyProfile.objects.filter(guardian=user)
            devices = Device.objects.select_related(
                'elderly', 'elderly__user', 'elderly__guardian', 'created_by'
            ).filter(elderly__in=elderly_profiles)
        
        device_id = self.request.query_params.get('device_id')
        if device_id:
            devices = devices.filter(device_id=device_id)
        
        elderly_id = self.request.query_params.get('elderly_id')
        if elderly_id:
            devices = devices.filter(elderly__id=elderly_id)
        
        return devices
    
    def get_serializer_class(self):
        return DeviceCreateSerializer if self.action == 'create' else DeviceSerializer
    
    @action(detail=False, methods=['post'])
    def bind_by_device_id(self, request):
        """
        监护人通过设备ID绑定设备到老人档案
        """
        user = request.user
        
        if user.role != 'guardian':
            return Response({'error': '只有监护人可以绑定设备'}, status=status.HTTP_403_FORBIDDEN)
        
        device_id = request.data.get('device_id')
        elderly_id = request.data.get('elderly_id')
        
        if not device_id:
            return Response({'error': '设备ID不能为空'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not elderly_id:
            return Response({'error': '老人ID不能为空'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            device = Device.objects.get(device_id=device_id)
        except Device.DoesNotExist:
            return Response({'error': '设备ID不存在'}, status=status.HTTP_404_NOT_FOUND)
        
        try:
            elderly = ElderlyProfile.objects.get(id=elderly_id)
        except ElderlyProfile.DoesNotExist:
            return Response({'error': '老人档案不存在'}, status=status.HTTP_404_NOT_FOUND)
        
        # 权限检查：如果guardian不为null，必须是当前用户；如果guardian为null，允许绑定
        if elderly.guardian and elderly.guardian != user:
            return Response({'error': '该老人档案已被其他监护人管理'}, status=status.HTTP_403_FORBIDDEN)
        
        # 如果设备已绑定到其他老人，允许重新绑定（解除旧绑定）
        if device.elderly and device.elderly.id != elderly_id:
            # 解除设备的旧绑定（设备可以重新绑定到其他老人）
            pass  # 直接覆盖绑定即可
        
        # 如果老人已经有其他设备，先解除旧设备的绑定
        try:
            old_device = elderly.device
            if old_device and old_device.id != device.id:
                # 解除老人的旧设备绑定（允许一个老人有多个设备，但一个设备只能绑定一个老人）
                old_device.elderly = None
                old_device.save()
        except ElderlyProfile.device.RelatedObjectDoesNotExist:
            pass  # 老人还没有设备，直接绑定即可
        
        # 绑定设备到老人
        device.elderly = elderly
        device.save()
        
        # 只有监护人角色才能设置guardian，老人角色不能设置
        # 如果老人档案的guardian为null，且当前用户是监护人角色，设置为当前监护人
        # 这确保监护人能够看到绑定设备的警报（包括SOS求救）
        if not elderly.guardian and user.role == 'guardian':
            elderly.guardian = user
            elderly.save()
        
        return Response(DeviceSerializer(device).data)
    
    @action(detail=True, methods=['post'])
    def bind(self, request, pk=None):
        device = self.get_object()
        device_id = request.data.get('device_id')
        device_type = request.data.get('device_type')
        
        if device_id and device_id != device.device_id:
            if Device.objects.filter(device_id=device_id).exclude(pk=device.pk).exists():
                return Response({'error': '设备ID已被使用'}, status=status.HTTP_400_BAD_REQUEST)
            device.device_id = device_id
        
        if device_type:
            # 验证设备类型是否有效
            valid_device_types = ['smart_bracelet', 'phone']
            if device_type not in valid_device_types:
                return Response(
                    {'error': f'无效的设备类型，只支持: {", ".join(valid_device_types)}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            device.device_type = device_type
        
        device.save()
        
        # 绑定/更新设备时，更新设备状态（根据最后在线时间判断）
        device.update_status()
        
        return Response(DeviceSerializer(device).data)
    
    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """获取设备最新状态"""
        device = self.get_object()
        device.update_status()
        return Response(DeviceSerializer(device).data)

