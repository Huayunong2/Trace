"""
定位序列化器
"""
from rest_framework import serializers
from .models import Location, LocationCache
from apps.devices.serializers import DeviceSerializer


class LocationSerializer(serializers.ModelSerializer):
    """位置记录序列化器"""
    device = DeviceSerializer(read_only=True)
    
    class Meta:
        model = Location
        fields = '__all__'
        read_only_fields = ['created_at']


class LocationCreateSerializer(serializers.Serializer):
    """位置创建序列化器（设备端上传）"""
    device_id = serializers.CharField(max_length=64)
    latitude = serializers.DecimalField(max_digits=10, decimal_places=7)
    longitude = serializers.DecimalField(max_digits=10, decimal_places=7)
    accuracy = serializers.FloatField(required=False)
    altitude = serializers.FloatField(required=False)
    speed = serializers.FloatField(required=False)
    heading = serializers.FloatField(required=False)
    battery_level = serializers.IntegerField(required=False)
    location_type = serializers.ChoiceField(choices=['gps', 'lbs', 'wifi'], default='gps')
    
    def create(self, validated_data):
        from apps.devices.models import Device
        from django.utils import timezone
        
        device_id = validated_data.pop('device_id')
        battery_level = validated_data.pop('battery_level', None)
        # 如果前端传入了address，使用前端的address；否则后端会通过逆地理编码获取
        address = validated_data.pop('address', '')
        
        try:
            device = Device.objects.get(device_id=device_id, is_active=True)
        except Device.DoesNotExist:
            raise serializers.ValidationError('设备不存在或未激活')
        
        # 更新设备状态和时间
        device.last_online_time = timezone.now()
        device.last_location_time = timezone.now()
        
        # 更新电量信息（如果提供了）
        if battery_level is not None:
            device.battery_level = max(0, min(100, int(battery_level)))  # 确保电量在0-100范围内
        
        # 设备状态会在views.py的upload方法中根据电量情况更新
        # 这里先设置为online，后续会根据电量调整
        device.status = 'online'
        device.save()
        
        # 创建位置记录（如果前端有地址就使用，否则Location.save()会自动通过逆地理编码获取）
        location = Location(device=device, address=address or '', **validated_data)
        # 调用save()以触发自动逆地理编码（如果address为空）
        location.save()
        
        # 缓存位置到Redis
        from .utils import cache_location
        cache_location(device_id, {
            'latitude': float(location.latitude),
            'longitude': float(location.longitude),
            'address': location.address,
            'recorded_at': location.recorded_at.isoformat(),
        })
        
        return location


class LocationCacheSerializer(serializers.ModelSerializer):
    """位置缓存序列化器"""
    
    class Meta:
        model = LocationCache
        fields = '__all__'

