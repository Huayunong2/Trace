"""
用户管理单元测试
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import ElderlyProfile

User = get_user_model()


class UserModelTest(TestCase):
    """用户模型测试"""
    
    def setUp(self):
        """测试前置设置"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            role='guardian'
        )
    
    def test_user_creation(self):
        """测试用户创建"""
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.role, 'guardian')
        self.assertTrue(self.user.is_active)
    
    def test_user_str(self):
        """测试用户字符串表示"""
        self.assertIn('testuser', str(self.user))
        self.assertIn('监护人', str(self.user))


class ElderlyProfileTest(TestCase):
    """老人档案测试"""
    
    def setUp(self):
        """测试前置设置"""
        self.guardian = User.objects.create_user(
            username='guardian',
            role='guardian'
        )
        self.elderly_user = User.objects.create_user(
            username='elderly',
            role='elderly'
        )
    
    def test_elderly_profile_creation_by_guardian(self):
        """测试监护人创建老人档案"""
        profile = ElderlyProfile.objects.create(
            guardian=self.guardian,
            name='测试老人',
            emergency_contact='联系人',
            emergency_phone='13800138000',
            address='测试地址'
        )
        self.assertEqual(profile.guardian, self.guardian)
        self.assertIsNone(profile.user)
        self.assertEqual(profile.name, '测试老人')
    
    def test_elderly_profile_creation_by_elderly(self):
        """测试老人创建自己的档案"""
        profile = ElderlyProfile.objects.create(
            user=self.elderly_user,
            name='测试老人',
            emergency_contact='联系人',
            emergency_phone='13800138000',
            address='测试地址'
        )
        self.assertEqual(profile.user, self.elderly_user)
        self.assertIsNone(profile.guardian)


class UserAPITest(TestCase):
    """用户API测试"""
    
    def setUp(self):
        """测试前置设置"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123',
            role='system_admin'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_get_user_list(self):
        """测试获取用户列表"""
        response = self.client.get('/api/auth/users/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_get_user_detail(self):
        """测试获取用户详情"""
        response = self.client.get(f'/api/auth/users/{self.user.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.user.id)

