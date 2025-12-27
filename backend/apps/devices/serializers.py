"""
设备序列化器
"""
from rest_framework import serializers
from .models import Device
from apps.users.serializers import ElderlyProfileSerializer


class DeviceSerializer(serializers.ModelSerializer):
    """设备序列化器"""
    elderly = ElderlyProfileSerializer(read_only=True)
    
    class Meta:
        model = Device
        fields = '__all__'
        read_only_fields = ['device_id', 'created_at', 'updated_at']


class DeviceCreateSerializer(serializers.ModelSerializer):
    """设备创建序列化器"""
    elderly_id = serializers.IntegerField(write_only=True)
    device_type = serializers.ChoiceField(
        choices=[('smart_bracelet', '智能手环'), ('phone', '手机')],
        default='smart_bracelet'
    )
    
    class Meta:
        model = Device
        fields = ['id', 'elderly_id', 'name', 'device_type', 'device_id']
        read_only_fields = ['id', 'device_id']
    
    def create(self, validated_data):
        from apps.users.models import ElderlyProfile
        
        elderly_id = validated_data.pop('elderly_id')
        user = self.context['request'].user
        
        try:
            elderly = ElderlyProfile.objects.get(id=elderly_id)
        except ElderlyProfile.DoesNotExist:
            raise serializers.ValidationError('老人档案不存在')
        
        # 权限验证
        if user.role == 'elderly':
            # 老人角色：只能为自己的档案创建设备
            if elderly.user != user:
                raise serializers.ValidationError('只能为自己的档案创建设备')
        else:
            # 监护人角色：只能为自己管理的老人档案创建设备
            if elderly.guardian != user:
                raise serializers.ValidationError('无权限为该老人创建设备')
        
        # 允许一个老人有多个设备，不限制
        # 设备通过elderly字段关联到老人，一个设备只能绑定一个老人
        # 记录创建设备的用户，用于后续查询（如果数据库已迁移）
        try:
            # 尝试设置 created_by 字段
            device = Device.objects.create(elderly=elderly, created_by=user, **validated_data)
        except Exception:
            # 如果 created_by 字段不存在（数据库未迁移），不设置该字段
            device = Device.objects.create(elderly=elderly, **validated_data)
        return device

