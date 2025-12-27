"""
设备管理模型
"""
import uuid
from django.db import models
from django.utils import timezone
from apps.users.models import ElderlyProfile


def generate_device_id():
    """生成设备ID"""
    return str(uuid.uuid4())


class Device(models.Model):
    """
    定位设备模型
    """
    STATUS_CHOICES = [
        ('online', '在线'),
        ('offline', '离线'),
        ('low_battery', '低电量'),
        ('error', '故障'),
    ]
    
    device_id = models.CharField('设备ID', max_length=64, unique=True, default=generate_device_id)
    elderly = models.OneToOneField(ElderlyProfile, on_delete=models.SET_NULL, related_name='device', verbose_name='关联老人', null=True, blank=True)
    created_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, related_name='created_devices', verbose_name='创建用户', null=True, blank=True)
    name = models.CharField('设备名称', max_length=50, default='定位设备')
    device_type = models.CharField('设备类型', max_length=20, choices=[
        ('smart_bracelet', '智能手环'),
        ('phone', '手机'),
    ], default='smart_bracelet')
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='offline')
    battery_level = models.IntegerField('电量', default=100)
    last_location_time = models.DateTimeField('最后定位时间', null=True, blank=True)
    last_online_time = models.DateTimeField('最后在线时间', null=True, blank=True)
    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        db_table = 'devices'
        verbose_name = '设备'
        verbose_name_plural = '设备'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} ({self.device_id})"
    
    def update_status(self):
        """更新设备状态"""
        from django.utils import timezone
        
        now = timezone.now()
        offline_threshold = 300  # 5分钟未上传位置视为离线
        low_battery_threshold = 20  # 电量低于20%视为低电量
        
        # 检查离线状态
        if self.last_online_time:
            offline_seconds = (now - self.last_online_time).total_seconds()
            if offline_seconds > offline_threshold:
                self.status = 'offline'
            elif offline_seconds <= offline_threshold and self.status == 'offline':
                self.status = 'online'
        
        # 检查低电量（只有在设备在线时才检查）
        if self.battery_level is not None and self.status != 'offline':
            if self.battery_level < low_battery_threshold:
                self.status = 'low_battery'
            elif self.battery_level >= low_battery_threshold and self.status == 'low_battery':
                # 电量恢复到正常水平，更新为在线状态
                self.status = 'online'
        
        self.save()

