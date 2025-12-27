"""
设备管理单元测试
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.users.models import ElderlyProfile
from .models import Device

User = get_user_model()


class DeviceModelTest(TestCase):
    """设备模型测试"""
    
    def setUp(self):
        """测试前置设置"""
        self.elderly_user = User.objects.create_user(
            username='elderly',
            role='elderly'
        )
        self.elderly_profile = ElderlyProfile.objects.create(
            user=self.elderly_user,
            name='测试老人',
            emergency_contact='联系人',
            emergency_phone='13800138000',
            address='测试地址'
        )
    
    def test_device_creation(self):
        """测试设备创建"""
        device = Device.objects.create(
            elderly=self.elderly_profile,
            name='测试设备',
            device_type='smart_bracelet'
        )
        self.assertIsNotNone(device.device_id)
        self.assertEqual(device.elderly, self.elderly_profile)
        self.assertEqual(device.name, '测试设备')
        self.assertTrue(len(device.device_id) > 0)  # UUID应该是非空的
    
    def test_device_id_unique(self):
        """测试设备ID唯一性"""
        device1 = Device.objects.create(
            elderly=self.elderly_profile,
            name='设备1',
            device_type='smart_bracelet'
        )
        device2 = Device.objects.create(
            elderly=self.elderly_profile,
            name='设备2',
            device_type='phone'
        )
        self.assertNotEqual(device1.device_id, device2.device_id)

