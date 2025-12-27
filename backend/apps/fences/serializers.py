"""
围栏序列化器
"""
from rest_framework import serializers
from .models import Fence, FenceViolationLog
from apps.devices.serializers import DeviceSerializer
from apps.locations.serializers import LocationSerializer


class FenceSerializer(serializers.ModelSerializer):
    """围栏序列化器"""
    device = DeviceSerializer(read_only=True)
    
    class Meta:
        model = Fence
        fields = '__all__'
        read_only_fields = ['violation_count', 'last_violation_time', 'created_at', 'updated_at']
    
    def update(self, instance, validated_data):
        # 允许更新围栏信息
        instance.name = validated_data.get('name', instance.name)
        instance.center_latitude = validated_data.get('center_latitude', instance.center_latitude)
        instance.center_longitude = validated_data.get('center_longitude', instance.center_longitude)
        instance.radius = validated_data.get('radius', instance.radius)
        instance.address = validated_data.get('address', instance.address)
        instance.save()
        return instance


class FenceCreateSerializer(serializers.ModelSerializer):
    """围栏创建序列化器"""
    device_id = serializers.CharField(write_only=True)
    
    class Meta:
        model = Fence
        fields = ['device_id', 'name', 'center_latitude', 'center_longitude', 'radius', 'address']
    
    def create(self, validated_data):
        from apps.devices.models import Device
        from rest_framework import serializers as drf_serializers
        
        device_id = validated_data.pop('device_id')
        user = self.context['request'].user
        
        # 查找设备，并验证权限
        try:
            device = Device.objects.get(device_id=device_id)
        except Device.DoesNotExist:
            raise drf_serializers.ValidationError({'device_id': f'设备不存在（device_id: {device_id}）'})
        
        # 验证用户是否有权限访问该设备
        from apps.users.models import ElderlyProfile
        
        # 如果是老人角色，检查设备是否已绑定监护人
        if user.role == 'elderly':
            if not device.elderly:
                raise drf_serializers.ValidationError({
                    'device_id': '设备未关联到老人档案'
                })
            if not device.elderly.guardian:
                raise drf_serializers.ValidationError({
                    'device_id': '设备尚未绑定监护人，请先让监护人绑定设备'
                })
        else:
            # 监护人角色：检查设备是否关联到自己管理的老人
            if not device.elderly:
                raise drf_serializers.ValidationError({
                    'device_id': '设备未关联到老人'
                })
            elderly_profiles = ElderlyProfile.objects.filter(guardian=user)
            if not elderly_profiles.filter(id=device.elderly.id).exists():
                raise drf_serializers.ValidationError({
                    'device_id': '无权限访问该设备'
                })
        
        fence = Fence.objects.create(device=device, **validated_data)
        return fence


class FenceViolationLogSerializer(serializers.ModelSerializer):
    """围栏越界日志序列化器"""
    fence = FenceSerializer(read_only=True)
    location = LocationSerializer(read_only=True)
    
    class Meta:
        model = FenceViolationLog
        fields = '__all__'

