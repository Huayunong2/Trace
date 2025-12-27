"""
电子围栏单元测试
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.users.models import ElderlyProfile
from apps.devices.models import Device
from .models import Fence

User = get_user_model()


class FenceModelTest(TestCase):
    """围栏模型测试"""
    
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
        self.device = Device.objects.create(
            elderly=self.elderly_profile,
            name='测试设备',
            device_type='smart_bracelet'
        )
    
    def test_fence_creation(self):
        """测试围栏创建"""
        fence = Fence.objects.create(
            device=self.device,
            name='测试围栏',
            center_latitude=39.908823,
            center_longitude=116.397470,
            radius=500,
            address='测试地址'
        )
        self.assertEqual(fence.device, self.device)
        self.assertEqual(fence.name, '测试围栏')
        self.assertEqual(fence.radius, 500)
        self.assertTrue(fence.is_active)
    
    def test_fence_violation_check(self):
        """测试围栏越界检查"""
        fence = Fence.objects.create(
            device=self.device,
            name='测试围栏',
            center_latitude=39.908823,
            center_longitude=116.397470,
            radius=500,  # 500米半径
            address='测试地址'
        )
        
        # 测试点在围栏内（距离约100米）
        is_violation1, distance1 = fence.check_violation(39.909523, 116.397470)
        self.assertFalse(is_violation1)
        self.assertLess(distance1, 500)
        
        # 测试点在围栏外（距离约10公里）
        is_violation2, distance2 = fence.check_violation(39.978823, 116.397470)
        self.assertTrue(is_violation2)
        self.assertGreater(distance2, 500)

