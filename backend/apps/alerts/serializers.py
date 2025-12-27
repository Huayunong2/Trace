"""
预警序列化器
"""
from rest_framework import serializers
from .models import Alert
from apps.devices.serializers import DeviceSerializer
from apps.locations.serializers import LocationSerializer
from apps.users.serializers import UserSerializer


class AlertSerializer(serializers.ModelSerializer):
    """预警序列化器"""
    device = DeviceSerializer(read_only=True)
    location = LocationSerializer(read_only=True)
    handled_by = UserSerializer(read_only=True)
    
    class Meta:
        model = Alert
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class AlertHandleSerializer(serializers.Serializer):
    """预警处理序列化器"""
    note = serializers.CharField(required=False, allow_blank=True, help_text='处理备注')

