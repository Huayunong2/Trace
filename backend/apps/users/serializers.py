"""
用户序列化器
"""
from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User, ElderlyProfile, SubscribeMessage


class UserSerializer(serializers.ModelSerializer):
    """用户序列化器"""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'phone', 'role', 'avatar', 'is_active', 'openid', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ElderlyProfileSerializer(serializers.ModelSerializer):
    """老人档案序列化器"""
    guardian = UserSerializer(read_only=True)
    device = serializers.SerializerMethodField()
    
    class Meta:
        model = ElderlyProfile
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']
    
    def get_device(self, obj):
        """获取关联的设备信息"""
        try:
            # 使用select_related优化查询，避免N+1问题
            device = obj.device
            if device:
                return {
                    'device_id': device.device_id,
                    'name': device.name,
                    'device_type': device.device_type,
                    'status': device.status,
                    'is_active': device.is_active
                }
            return None
        except Exception:
            return None


class LoginSerializer(serializers.Serializer):
    """登录序列化器"""
    code = serializers.CharField(required=True, help_text='微信登录code')
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES, required=False, default='guardian', help_text='选择的角色')
    
    def validate(self, attrs):
        code = attrs.get('code')
        return attrs


class RegisterSerializer(serializers.Serializer):
    """注册序列化器"""
    username = serializers.CharField(max_length=150)
    phone = serializers.CharField(max_length=11)
    password = serializers.CharField(write_only=True, min_length=6)
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES, default='guardian')
    
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            phone=validated_data['phone'],
            password=validated_data['password'],
            role=validated_data.get('role', 'guardian')
        )
        return user


class SubscribeMessageSerializer(serializers.ModelSerializer):
    """订阅消息序列化器"""
    
    class Meta:
        model = SubscribeMessage
        fields = ['id', 'template_id', 'subscribe_status', 'subscribed_at', 'updated_at']
        read_only_fields = ['id', 'subscribed_at', 'updated_at']
