"""
系统管理序列化器
"""
from rest_framework import serializers
from .models import SystemConfig


class SystemConfigSerializer(serializers.ModelSerializer):
    """系统配置序列化器"""
    typed_value = serializers.SerializerMethodField()
    
    class Meta:
        model = SystemConfig
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def get_typed_value(self, obj):
        """获取类型转换后的值"""
        return obj.get_typed_value()

