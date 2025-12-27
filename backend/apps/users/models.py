"""
用户管理模型
"""
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    """
    用户模型 - 支持多种角色（监护人、社区管理员、系统管理员）
    """
    ROLE_CHOICES = [
        ('guardian', '监护人'),
        ('elderly', '老人'),
        ('community_admin', '社区管理员'),
        ('system_admin', '系统管理员'),
    ]
    
    role = models.CharField('角色', max_length=20, choices=ROLE_CHOICES, default='guardian')
    phone = models.CharField('手机号', max_length=11, unique=True, null=True, blank=True)
    openid = models.CharField('微信OpenID', max_length=128, unique=True, null=True, blank=True)
    avatar = models.ImageField('头像', upload_to='avatars/', null=True, blank=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'users'
        verbose_name = '用户'
        verbose_name_plural = '用户'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class ElderlyProfile(models.Model):
    """
    老人档案信息
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='elderly_profile',
        null=True,
        blank=True,
        verbose_name='关联老人用户'
    )  # 老人用户直接关联
    guardian = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='elderly_profiles', verbose_name='监护人', null=True, blank=True)
    name = models.CharField('姓名', max_length=50)
    age = models.IntegerField('年龄', null=True, blank=True)
    gender = models.CharField('性别', max_length=10, choices=[('male', '男'), ('female', '女')], null=True, blank=True)
    medical_history = models.TextField('病史', blank=True)
    emergency_contact = models.CharField('紧急联系人', max_length=50)
    emergency_phone = models.CharField('紧急联系电话', max_length=11)
    address = models.CharField('常住地址', max_length=200)
    photo = models.ImageField('近照', upload_to='elderly_photos/', null=True, blank=True)
    id_card = models.CharField('身份证号', max_length=18, null=True, blank=True)
    notes = models.TextField('备注', blank=True)
    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'elderly_profiles'
        verbose_name = '老人档案'
        verbose_name_plural = '老人档案'
        ordering = ['-created_at']
    
    def __str__(self):
        if self.guardian:
            return f"{self.name} - {self.guardian.username}"
        else:
            return f"{self.name} - 未绑定监护人"


class SubscribeMessage(models.Model):
    """
    用户订阅消息记录
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscribe_messages', verbose_name='用户')
    template_id = models.CharField('模板ID', max_length=100)
    subscribe_status = models.BooleanField('订阅状态', default=True)  # True表示已订阅，False表示已拒绝
    subscribed_at = models.DateTimeField('订阅时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'subscribe_messages'
        verbose_name = '订阅消息'
        verbose_name_plural = '订阅消息'
        unique_together = ['user', 'template_id']
        ordering = ['-subscribed_at']
    
    def __str__(self):
        status = '已订阅' if self.subscribe_status else '已拒绝'
        return f"{self.user.username} - {self.template_id} - {status}"
